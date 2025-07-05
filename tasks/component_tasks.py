"""
Individual Celery tasks for each component of the speech evaluation pipeline.
"""
import os
import json
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.core.celery_instance import celery_app
from database import (
    sync_engine_sqlalchemy,
    SQLModelSession,
    EvaluationComponentResult,
    EvaluationComponentType,
    TaskStatus,
    BackgroundTask, 
    PracticeSession, 
    PracticeSessionCreate
)
from sqlmodel import select
from whisper_engine import transcribe
from language_analyzer import language_analyzer
from grammar_corrector import get_corrected_grammar, get_speech_feedback, compare_answers

logger = logging.getLogger(__name__)

def update_component_task_status_sync(component_id: int, status: TaskStatus, status_message: Optional[str] = None, result: Optional[Dict] = None, error: Optional[str] = None):
    """Update individual component task status in the database synchronously."""
    try:
        with SQLModelSession(sync_engine_sqlalchemy) as session:
            task_entry = session.get(EvaluationComponentResult, component_id)
            if task_entry:
                task_entry.status = status
                if status_message:
                    task_entry.status_message = status_message
                task_entry.updated_at = datetime.now(timezone.utc)
                if result:
                    task_entry.result = json.dumps(result)
                if error:
                    task_entry.error_message = error
                if status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                    task_entry.completed_at = datetime.now(timezone.utc)
                session.add(task_entry)
                session.commit()
    except Exception as e:
        logger.error(f"Error updating component task status for component_id {component_id}: {e}", exc_info=True)

# --- Component Tasks ---

@celery_app.task(bind=True, name="tasks.component_tasks.transcribe_audio_task")
def transcribe_audio_task(self, component_id: int, audio_file_path: str, parent_task_id: str, question: str, ideal_answer: str, llm_model: str):
    logger.info(f"Task {self.request.id} (Component ID: {component_id}): Starting transcription.")
    update_component_task_status_sync(component_id, TaskStatus.PROCESSING, status_message="Transcription in progress...")
    try:
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

        transcript, flagged_words = transcribe(audio_file_path)
        if not transcript:
            raise ValueError("Transcription failed: No speech detected.")

        result_data = {"transcript": transcript, "flagged_words": flagged_words}
        update_component_task_status_sync(component_id, TaskStatus.COMPLETED, status_message="Transcription complete.", result=result_data)
        logger.info(f"Task {self.request.id}: Transcription successful.")

        return {"status": "COMPLETED", "message": "Transcription finished."}
    except Exception as e:
        error_msg = f"Transcription error: {e}"
        logger.error(f"Task {self.request.id}: {error_msg}", exc_info=True)
        update_component_task_status_sync(component_id, TaskStatus.FAILED, status_message=error_msg, error=error_msg)

def _run_component_task(task_id, component_id, status_message, analysis_func, *args):
    logger.info(f"--- INSIDE _run_component_task ---")
    logger.info(f"Task {task_id} (Component ID: {component_id}): {status_message}")
    update_component_task_status_sync(component_id, TaskStatus.PROCESSING, status_message=f"{status_message}...")
    try:
        result = analysis_func(*args)
        update_component_task_status_sync(component_id, TaskStatus.COMPLETED, status_message="Analysis complete.", result=result)
        return result
    except Exception as e:
        error_msg = f"{status_message} error: {e}"
        logger.error(f"Task {task_id}: {error_msg}", exc_info=True)
        update_component_task_status_sync(component_id, TaskStatus.FAILED, status_message=error_msg, error=error_msg)

@celery_app.task(bind=True, name="tasks.component_tasks.audio_features_task")
def extract_audio_features_task(self, component_id: int, audio_file_path: str):
    return _run_component_task(self.request.id, component_id, "Audio feature extraction", lambda: asyncio.run(language_analyzer.analyze_audio_features(audio_file_path)))

@celery_app.task(bind=True, name="tasks.component_tasks.emotion_text_task")
def analyze_text_emotion_task(self, component_id: int, transcript: str):
    return _run_component_task(self.request.id, component_id, "Text emotion analysis", lambda: asyncio.run(language_analyzer.analyze_emotion(transcript)))

@celery_app.task(bind=True, name="tasks.component_tasks.sentiment_text_task")
def analyze_text_sentiment_task(self, component_id: int, transcript: str):
    return _run_component_task(self.request.id, component_id, "Text sentiment analysis", language_analyzer.analyze_sentiment, transcript)

@celery_app.task(bind=True, name="tasks.component_tasks.linguistic_text_task")
def analyze_linguistic_features_task(self, component_id: int, transcript: str):
    return _run_component_task(self.request.id, component_id, "Linguistic feature analysis", language_analyzer.analyze_linguistic_features, transcript)

@celery_app.task(bind=True, name="tasks.component_tasks.grammar_task")
def evaluate_grammar_task(self, component_id: int, transcript: str, question: str, model: str):
    result = get_corrected_grammar(transcript, question=question, model=model)
    return _run_component_task(self.request.id, component_id, "Grammar evaluation", lambda: {"grammar_feedback": result})

@celery_app.task(bind=True, name="tasks.component_tasks.content_comparison_task")
def evaluate_content_task(self, component_id: int, transcript: str, ideal_answer: str, question: str, model: str):
    result = compare_answers(transcript, ideal_answer, question, model=model)
    return _run_component_task(self.request.id, component_id, "Content evaluation", lambda: {"content_evaluation": result})

@celery_app.task(bind=True, name="tasks.component_tasks.pronunciation_task")
def evaluate_pronunciation_task(self, component_id: int, transcript: str, flagged_words: list, question: str, model: str):
    result = get_speech_feedback(flagged_words, transcript=transcript, question=question, model=model)
    return _run_component_task(self.request.id, component_id, "Pronunciation evaluation", lambda: {"pronunciation_feedback": result})

# --- Aggregation Task ---

def _calculate_rating(components: list) -> float:
    score = 3.0
    try:
        # Simplified scoring logic
        grammar_comp = next((c for c in components if c.component_type == EvaluationComponentType.GRAMMAR and c.result), None)
        if grammar_comp and len(json.loads(grammar_comp.result).get("grammar_feedback", "")) < 300: score += 1.0
        
        content_comp = next((c for c in components if c.component_type == EvaluationComponentType.CONTENT_COMPARISON and c.result), None)
        if content_comp and len(json.loads(content_comp.result).get("content_evaluation", "")) < 500: score += 1.0
    except Exception as e:
        logger.error(f"Error calculating rating: {e}")
    return max(1.0, min(5.0, round(score, 1)))

@celery_app.task(bind=True, name="tasks.component_tasks.create_final_summary_task")
def create_final_summary_task(self, parent_task_id: str):
    logger.info(f"Starting final summary for parent_task_id: {parent_task_id}")
    try:
        with SQLModelSession(sync_engine_sqlalchemy) as session:
            # Fetch all components, including failed ones, to get a complete picture
            stmt = select(EvaluationComponentResult).where(EvaluationComponentResult.parent_task_id == parent_task_id)
            all_components = session.exec(stmt).all()
            
            completed_components = [c for c in all_components if c.status == TaskStatus.COMPLETED]
            
            # Check if all expected components are present and completed
            if len(completed_components) < len(EvaluationComponentType):
                failed_count = sum(1 for c in all_components if c.status == TaskStatus.FAILED)
                logger.warning(f"Not all components completed successfully for parent task {parent_task_id}. "
                               f"Found {len(completed_components)} completed, {failed_count} failed out of {len(EvaluationComponentType)} total.")
                # Decide if you should still proceed or fail the whole task.
                # For now, we'll proceed with what we have but this could be a failure condition.

            parent_task = session.exec(select(BackgroundTask).where(BackgroundTask.task_id == parent_task_id)).first()
            if not parent_task:
                raise ValueError(f"Parent task {parent_task_id} not found.")
            
            results = {comp.component_type.value: json.loads(comp.result) for comp in completed_components if comp.result}
            transcript = results.get(EvaluationComponentType.TRANSCRIPTION.value, {}).get("transcript", "N/A")

            final_session_data = PracticeSessionCreate(
                parent_task_id=parent_task_id,
                user_id=parent_task.user_id,
                topic=parent_task.topic,
                difficulty=parent_task.difficulty,
                question=parent_task.question,
                ideal_answer=parent_task.ideal_answer,
                transcript=transcript,
                grammar_feedback=results.get(EvaluationComponentType.GRAMMAR.value, {}).get("grammar_feedback"),
                pronunciation_feedback=results.get(EvaluationComponentType.PRONUNCIATION.value, {}).get("pronunciation_feedback"),
                content_evaluation=results.get(EvaluationComponentType.CONTENT_COMPARISON.value, {}).get("content_evaluation"),
                audio_features=json.dumps(results.get(EvaluationComponentType.AUDIO_FEATURES.value)),
                linguistic_features=json.dumps(results.get(EvaluationComponentType.LINGUISTIC_TEXT.value)),
                sentiment_analysis=json.dumps(results.get(EvaluationComponentType.SENTIMENT_TEXT.value)),
                emotion_analysis=json.dumps(results.get(EvaluationComponentType.EMOTION_TEXT.value)),
                rating=_calculate_rating(completed_components)
            )
            
            db_practice_session = PracticeSession.from_orm(final_session_data)
            session.add(db_practice_session)
            session.commit()
            session.refresh(db_practice_session)
            
            parent_task.status = TaskStatus.COMPLETED
            parent_task.status_message = f"Evaluation complete. View results in session {db_practice_session.id}."
            parent_task.progress = 100
            parent_task.completed_at = datetime.now(timezone.utc)
            parent_task.result = json.dumps({"practice_session_id": db_practice_session.id})
            session.add(parent_task)
            session.commit()
            
            logger.info(f"Successfully created PracticeSession {db_practice_session.id} and marked parent task {parent_task_id} as COMPLETED.")
    except Exception as e:
        logger.error(f"Error in create_final_summary_task for {parent_task_id}: {e}", exc_info=True)
        with SQLModelSession(sync_engine_sqlalchemy) as session:
            parent_task = session.exec(select(BackgroundTask).where(BackgroundTask.task_id == parent_task_id)).first()
            if parent_task:
                parent_task.status = TaskStatus.FAILED
                parent_task.error_message = "Failed to create final summary."
                session.add(parent_task)
                session.commit()