from fastapi import FastAPI, HTTPException, File, UploadFile, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import shutil
import os
import json
import uuid
from pathlib import Path
from datetime import datetime
import logging

from database import (
    init_db, get_async_session, User, UserCreate, UserRead,
    PracticeSession, PracticeSessionRead,
    BackgroundTask, BackgroundTaskCreate, BackgroundTaskRead, TaskStatus,
    EvaluationComponentResult, EvaluationComponentResultCreate, EvaluationComponentType
)
from security import (
    get_password_hash, verify_password,
    create_access_token, decode_access_token,
    create_refresh_token
)
from grammar_corrector import generate_question_and_answer
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.celery_instance import celery_app
from tasks.component_tasks import (
    transcribe_audio_task,
    extract_audio_features_task,
    create_final_summary_task
)

# --- Pydantic Models ---

class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class QuestionGenerationRequest(BaseModel):
    topic: str
    difficulty: str
    model: str = "mistral:latest"

class QuestionResponse(BaseModel):
    question: str
    ideal_answer: str

class ComponentStatusDetail(BaseModel):
    component_id: int
    component_type: str
    status: str
    status_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    updated_at: datetime

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: int
    status_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    components: List[ComponentStatusDetail]

# --- FastAPI App Instance ---

app = FastAPI(
    title="VaakShakti AI - Holistic Language Assistant",
    description="Comprehensive API for VaakShakti AI speech tutor and language analysis platform.",
    version="1.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO)

TEMP_UPLOAD_DIR = Path("/app/temp_uploads")
TEMP_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@app.on_event("startup")
async def on_startup():
    await init_db()
    logger.info("Database initialized and application startup complete.")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")

async def get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_async_session)) -> User:
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    payload = decode_access_token(token)
    if payload is None or payload.get("sub") is None:
        raise credentials_exception
    user = (await session.exec(select(User).where(User.email == payload["sub"]))).first()
    if user is None:
        raise credentials_exception
    return user

# --- API Endpoints ---

@app.post("/api/v1/users/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(user_create: UserCreate, session: AsyncSession = Depends(get_async_session)):
    if (await session.exec(select(User).where(User.email == user_create.email))).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = User(
        email=user_create.email,
        full_name=user_create.full_name,
        hashed_password=get_password_hash(user_create.password)
    )
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user

@app.post("/api/v1/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_async_session)):
    logger.info(f"Login attempt for username: {form_data.username}")
    user = (await session.exec(select(User).where(User.email == form_data.username))).first()

    if not user:
        logger.warning(f"Login failed: User '{form_data.username}' not found.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    logger.info(f"User '{form_data.username}' found. Verifying password...")
    if not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Login failed: Incorrect password for user '{form_data.username}'.")
        # To prevent timing attacks, it's good practice to have similar responses for user not found and incorrect password.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    logger.info(f"Password verified for user '{form_data.username}'. Creating tokens.")
    return {
        "access_token": create_access_token(data={"sub": user.email}),
        "refresh_token": create_refresh_token(data={"sub": user.email}),
        "token_type": "bearer"
    }

@app.post("/api/v1/token/refresh", response_model=Token)
async def refresh_access_token(request: RefreshTokenRequest, session: AsyncSession = Depends(get_async_session)):
    payload = decode_access_token(request.refresh_token)
    if payload is None or payload.get("type") != "refresh" or payload.get("sub") is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    user = (await session.exec(select(User).where(User.email == payload["sub"]))).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return {
        "access_token": create_access_token(data={"sub": user.email}),
        "refresh_token": create_refresh_token(data={"sub": user.email}),
        "token_type": "bearer"
    }

@app.get("/api/v1/users/me", response_model=UserRead)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.post("/api/v1/logout")
async def logout(current_user: User = Depends(get_current_user)):
    # In a real-world scenario, you might want to invalidate the token
    # by adding it to a denylist in a database or cache (e.g., Redis).
    # For this example, we'll just return a success message.
    return {"message": "Logout successful"}

@app.post("/api/v1/questions/generate", response_model=QuestionResponse)
async def generate_question(request: QuestionGenerationRequest, current_user: User = Depends(get_current_user)):
    logger.info(f"Generating question for topic: {request.topic}, difficulty: {request.difficulty}")
    
    question, ideal_answer = generate_question_and_answer(request.topic, request.difficulty, request.model)
    
    if "Error:" in question or "Error:" in ideal_answer:
        raise HTTPException(status_code=500, detail="Failed to generate question from the language model.")
        
    return QuestionResponse(question=question, ideal_answer=ideal_answer)

@app.post("/api/v1/speech/evaluate", response_model=BackgroundTaskRead)
async def evaluate_speech_async(
    audio_file: UploadFile = File(...),
    topic: str = File(...),
    difficulty: str = File(...),
    question: str = File(...),
    ideal_answer: str = File(...),
    model: str = File("mistral:latest"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    parent_task_id = str(uuid.uuid4())
    try:
        temp_audio_path = str(TEMP_UPLOAD_DIR / f"audio_{parent_task_id}_{audio_file.filename}")
        with open(temp_audio_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)

        parent_task = BackgroundTask.from_orm(BackgroundTaskCreate(
            user_id=current_user.id, task_id=parent_task_id, task_type="master_speech_evaluation",
            topic=topic, difficulty=difficulty, question=question, ideal_answer=ideal_answer, model=model
        ))
        session.add(parent_task)
        await session.commit()
        await session.refresh(parent_task)

        component_types = [e for e in EvaluationComponentType]
        component_entries = [EvaluationComponentResult.from_orm(EvaluationComponentResultCreate(parent_task_id=parent_task_id, component_type=comp_type)) for comp_type in component_types]
        session.add_all(component_entries)
        await session.commit()

        for comp_entry in component_entries:
            await session.refresh(comp_entry)
            if comp_entry.component_type == EvaluationComponentType.TRANSCRIPTION:
                task = transcribe_audio_task.delay(comp_entry.id, temp_audio_path, parent_task_id, question, ideal_answer, model)
                logger.info(f"Dispatched transcribe_audio_task with ID: {task.id} for component ID: {comp_entry.id}")
            elif comp_entry.component_type == EvaluationComponentType.AUDIO_FEATURES:
                task = extract_audio_features_task.delay(comp_entry.id, temp_audio_path)
                logger.info(f"Dispatched extract_audio_features_task with ID: {task.id} for component ID: {comp_entry.id}")
        
        parent_task.status = TaskStatus.PROCESSING
        parent_task.status_message = "Initial audio analysis tasks dispatched."
        session.add(parent_task)
        await session.commit()
        await session.refresh(parent_task)
        return parent_task
    except Exception as e:
        logger.error(f"Error in /api/v1/speech/evaluate: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {e}")

@app.get("/api/v1/tasks/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(task_id: str, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_async_session)):
    parent_task = (await session.exec(select(BackgroundTask).where(BackgroundTask.task_id == task_id, BackgroundTask.user_id == current_user.id))).first()
    if not parent_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    components = (await session.exec(select(EvaluationComponentResult).where(EvaluationComponentResult.parent_task_id == task_id))).all()
    
    logger.info(f"Checking status for task {task_id}. Current status: {parent_task.status}")
    if parent_task.status == TaskStatus.PROCESSING:
        component_statuses = {c.component_type: c.status for c in components}
        logger.info(f"Component statuses: {component_statuses}")
        completed_count = sum(1 for status in component_statuses.values() if status == TaskStatus.COMPLETED)
        failed_count = sum(1 for status in component_statuses.values() if status == TaskStatus.FAILED)

        if failed_count > 0:
            parent_task.status = TaskStatus.FAILED
            parent_task.error_message = "One or more evaluation components failed."
        elif component_statuses.get(EvaluationComponentType.TRANSCRIPTION) == TaskStatus.COMPLETED and \
             component_statuses.get(EvaluationComponentType.AUDIO_FEATURES) == TaskStatus.COMPLETED and \
             not parent_task.result: # Use result field to track if text tasks were dispatched

            # Stage 2: Dispatch text-based analysis tasks
            transcription_comp = next((c for c in components if c.component_type == EvaluationComponentType.TRANSCRIPTION), None)
            if transcription_comp and transcription_comp.result:
                transcript_data = json.loads(transcription_comp.result)
                transcript = transcript_data.get("transcript")
                flagged_words = transcript_data.get("flagged_words")

                text_components = [c for c in components if c.component_type not in [EvaluationComponentType.TRANSCRIPTION, EvaluationComponentType.AUDIO_FEATURES]]
                for comp_entry in text_components:
                    task_name = f'tasks.component_tasks.{comp_entry.component_type.value}_task'
                    logger.info(f"Preparing to dispatch task: {task_name} for component ID: {comp_entry.id}")
                    args = [comp_entry.id, transcript]
                    
                    if comp_entry.component_type == EvaluationComponentType.GRAMMAR:
                        task_args = (*args, parent_task.question, parent_task.model)
                    elif comp_entry.component_type == EvaluationComponentType.CONTENT_COMPARISON:
                        task_args = (*args, parent_task.ideal_answer, parent_task.question, parent_task.model)
                    elif comp_entry.component_type == EvaluationComponentType.PRONUNCIATION:
                        task_args = (*args, flagged_words, parent_task.question, parent_task.model)
                    else:
                        task_args = args
                        
                    celery_app.send_task(task_name, args=task_args)
                    logger.info(f"Dispatched {comp_entry.component_type.value} task with name {task_name} (Component ID: {comp_entry.id})")
                
                parent_task.result = json.dumps({"text_tasks_dispatched": True}) # Mark as dispatched
                parent_task.status_message = "Text analysis tasks dispatched."
            else:
                parent_task.status = TaskStatus.FAILED
                parent_task.error_message = "Transcription result not found."

        elif completed_count == len(EvaluationComponentType):
            parent_task.status_message = "All components complete. Aggregating final results..."
            parent_task.progress = 95
            create_final_summary_task.delay(parent_task.task_id)
        else:
            parent_task.progress = int((completed_count / len(EvaluationComponentType)) * 90)
            parent_task.status_message = f"{completed_count}/{len(EvaluationComponentType)} components processed."

        session.add(parent_task)
        await session.commit()

    await session.refresh(parent_task)
    
    return TaskStatusResponse(
        task_id=parent_task.task_id, status=parent_task.status.value, progress=parent_task.progress,
        status_message=parent_task.status_message, result=json.loads(parent_task.result) if parent_task.result else None,
        error_message=parent_task.error_message, created_at=parent_task.created_at, updated_at=parent_task.updated_at,
        components=[{"component_id": c.id, "component_type": c.component_type.value, "status": c.status.value,
                     "status_message": c.status_message, "result": json.loads(c.result) if c.result else None,
                     "error_message": c.error_message, "updated_at": c.updated_at} for c in components]
    )

@app.get("/api/v1/users/me/history", response_model=List[PracticeSessionRead])
async def read_user_history(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_async_session)):
    return (await session.exec(select(PracticeSession).where(PracticeSession.user_id == current_user.id).order_by(PracticeSession.created_at.desc()))).all()

@app.get("/api/v1/sessions/{session_id}", response_model=PracticeSessionRead)
async def get_session_details(session_id: int, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_async_session)):
    session_record = (await session.exec(select(PracticeSession).where(PracticeSession.id == session_id, PracticeSession.user_id == current_user.id))).first()
    if not session_record:
        raise HTTPException(status_code=404, detail="Session not found")
    return session_record