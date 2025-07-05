import os
from sqlmodel import Field, Relationship, SQLModel # SQLModel base and field types
# Import AsyncSession from sqlalchemy.ext.asyncio for create_async_engine
from sqlalchemy.ext.asyncio import create_async_engine
# Import AsyncSession from SQLModel for the dependency injector
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession
from sqlalchemy import Column, Text, text # Import Column and Text
from sqlalchemy.dialects.postgresql import TIMESTAMP # Import TIMESTAMP for timezone support
from typing import List, Optional
import datetime
from enum import Enum

# 1. Database URL - Read from environment variable, with a fallback for local dev outside Docker
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://vaakshakti_user:vaakshakti_password@localhost:1211/vaakshakti_db")
# Note: The default fallback above uses the docker-compose credentials.
# When running IN Docker, the DATABASE_URL from docker-compose.yml will be used.

# Define the Async SQLAlchemy engine (to be used by SQLModel)
# `echo=True` is useful for debugging, it prints all SQL statements
async_engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# Synchronous engine for Celery tasks or scripts
SYNC_DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
from sqlalchemy import create_engine as sqlalchemy_create_engine
sync_engine_sqlalchemy = sqlalchemy_create_engine(SYNC_DATABASE_URL, echo=True)


# --- SQLModel Table Definitions ---

class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    last_login: Optional[datetime.datetime] = None
    is_active: bool = Field(default=True)

    # Relationships
    practice_sessions: List["PracticeSession"] = Relationship(back_populates="user")
    sessions: List["UserSession"] = Relationship(back_populates="user")
    bookings: List["BookingSlot"] = Relationship(back_populates="user")
    background_tasks: List["BackgroundTask"] = Relationship(back_populates="user")

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int
    created_at: datetime.datetime
    last_login: Optional[datetime.datetime] = None
    is_active: bool
    # email, full_name, bio, avatar_url are inherited from UserBase
    last_login: Optional[datetime.datetime] = None
    is_active: bool
    # We might not want to expose full_name or other details in every read scenario.
    # bio and avatar_url are inherited from UserBase.

class PracticeSessionBase(SQLModel):
    # Link to the parent task that generated this session
    parent_task_id: str = Field(index=True, unique=True)
    
    # Session metadata
    topic: str
    difficulty: str
    question: str
    ideal_answer: str
    transcript: str
    
    # Aggregated feedback results (as JSON strings or text)
    grammar_feedback: Optional[str] = Field(default=None, sa_column=Column(Text))
    pronunciation_feedback: Optional[str] = Field(default=None, sa_column=Column(Text))
    content_evaluation: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    # Aggregated scores and analysis data (as JSON strings)
    audio_features: Optional[str] = Field(default=None) # JSON
    linguistic_features: Optional[str] = Field(default=None) # JSON
    sentiment_analysis: Optional[str] = Field(default=None) # JSON
    emotion_analysis: Optional[str] = Field(default=None) # JSON
    
    # Overall calculated score
    rating: float = Field(default=0.0)
    
    # Timestamps
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow, sa_column=Column(TIMESTAMP(timezone=True), nullable=False))
    
    # Foreign Key to User
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")

class PracticeSession(PracticeSessionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationship
    user: Optional[User] = Relationship(back_populates="practice_sessions")

class PracticeSessionCreate(PracticeSessionBase):
    pass

class PracticeSessionRead(PracticeSessionBase):
    id: int
    # Optionally include user details if needed, e.g., user: UserRead

# --- Enums for Booking System ---
class BookingStatus(str, Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class SessionType(str, Enum):
    PRACTICE = "practice"
    INTERVIEW = "interview"
    EVALUATION = "evaluation"
    CONSULTATION = "consultation"

# --- User Session Management ---
class UserSessionBase(SQLModel):
    user_id: int = Field(foreign_key="user.id")
    session_token: str = Field(unique=True, index=True)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    expires_at: datetime.datetime
    is_active: bool = Field(default=True)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class UserSession(UserSessionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationship to User
    user: Optional[User] = Relationship(back_populates="sessions")

class UserSessionCreate(UserSessionBase):
    pass

class UserSessionRead(UserSessionBase):
    id: int

# --- Booking System ---
class BookingSlotBase(SQLModel):
    user_id: int = Field(foreign_key="user.id")
    scheduled_time: datetime.datetime
    duration_minutes: int = Field(default=30)
    session_type: SessionType
    status: BookingStatus = Field(default=BookingStatus.SCHEDULED)
    topic: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

class BookingSlot(BookingSlotBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationship to User
    user: Optional[User] = Relationship(back_populates="bookings")

class BookingSlotCreate(BookingSlotBase):
    pass

class BookingSlotRead(BookingSlotBase):
    id: int

class BookingSlotUpdate(SQLModel):
    scheduled_time: Optional[datetime.datetime] = None
    duration_minutes: Optional[int] = None
    session_type: Optional[SessionType] = None
    status: Optional[BookingStatus] = None
    topic: Optional[str] = None
    notes: Optional[str] = None

# The LanguageAnalysis table is now deprecated and has been removed.

# --- Background Task Tracking ---
class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class BackgroundTaskBase(SQLModel):
    user_id: int = Field(foreign_key="user.id")
    task_id: str = Field(unique=True, index=True)
    task_type: str  # e.g., "speech_evaluation", "language_analysis"
    
    # Add fields to store the initial context for the evaluation
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    question: Optional[str] = Field(default=None, sa_column=Column(Text))
    ideal_answer: Optional[str] = Field(default=None, sa_column=Column(Text))
    model: Optional[str] = None

    status: TaskStatus = Field(default=TaskStatus.PENDING)
    progress: int = Field(default=0)  # 0-100
    status_message: Optional[str] = Field(default="Task submitted...") # Human-readable status
    result: Optional[str] = None  # Can be used for a final summary ID or simple result
    error_message: Optional[str] = None
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow, sa_column=Column(TIMESTAMP(timezone=True), nullable=False))
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow, sa_column=Column(TIMESTAMP(timezone=True), nullable=False))
    completed_at: Optional[datetime.datetime] = Field(default=None, sa_column=Column(TIMESTAMP(timezone=True), nullable=True))

class BackgroundTask(BackgroundTaskBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationship to User
    user: Optional[User] = Relationship(back_populates="background_tasks")

class BackgroundTaskCreate(BackgroundTaskBase):
    pass

class BackgroundTaskRead(BackgroundTaskBase):
    id: int

# --- Evaluation Component Results ---
class EvaluationComponentType(str, Enum):
    TRANSCRIPTION = "transcription"
    AUDIO_FEATURES = "audio_features" # Prosody, pitch, etc.
    EMOTION_TEXT = "emotion_text"
    SENTIMENT_TEXT = "sentiment_text"
    LINGUISTIC_TEXT = "linguistic_text"
    GRAMMAR = "grammar"
    CONTENT_COMPARISON = "content_comparison"
    PRONUNCIATION = "pronunciation" # This might still be part of a larger text analysis or need audio

class EvaluationComponentResultBase(SQLModel):
    parent_task_id: str = Field(index=True) # Corresponds to BackgroundTask.task_id
    component_type: EvaluationComponentType
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    status_message: Optional[str] = Field(default="Component task submitted...")
    result: Optional[str] = None  # JSON string of the component's result
    error_message: Optional[str] = None
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow, sa_column=Column(TIMESTAMP(timezone=True), nullable=False))
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow, sa_column=Column(TIMESTAMP(timezone=True), nullable=False))
    completed_at: Optional[datetime.datetime] = Field(default=None, sa_column=Column(TIMESTAMP(timezone=True), nullable=True))

class EvaluationComponentResult(EvaluationComponentResultBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # No direct FK relationship to BackgroundTask to avoid complex ORM issues with task_id as string
    # We'll query by parent_task_id string.

class EvaluationComponentResultCreate(EvaluationComponentResultBase):
    pass

class EvaluationComponentResultRead(EvaluationComponentResultBase):
    id: int

# --- Database Initialization ---
async def create_db_and_tables():
    async with async_engine.begin() as conn:
        # Manually drop the old table with cascade to resolve dependency issues
        await conn.execute(text("DROP TABLE IF EXISTS languageanalysis CASCADE"))
        await conn.run_sync(SQLModel.metadata.drop_all) # Use this to drop tables if needed during dev
        await conn.run_sync(SQLModel.metadata.create_all)

# --- Dependency for getting an Async DB session ---
async def get_async_session() -> SQLModelAsyncSession: # Type hint now uses SQLModelAsyncSession
    async_session = SQLModelAsyncSession(async_engine, expire_on_commit=False) # Instantiate SQLModelAsyncSession
    try:
        yield async_session
    finally:
        await async_session.close()

# --- Dependency for getting a Synchronous DB session (for Celery tasks) ---
from sqlmodel import Session as SQLModelSession # Synchronous session

def get_sync_session() -> SQLModelSession:
    with SQLModelSession(sync_engine_sqlalchemy) as session: # Use the standard SQLAlchemy engine
        yield session

# To be called on application startup
async def init_db():
    await create_db_and_tables()