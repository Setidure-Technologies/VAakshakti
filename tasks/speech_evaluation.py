"""
Background tasks for speech evaluation and analysis
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timezone # Added timezone
import tempfile
import shutil

from celery import current_task
from app.core.celery_instance import celery_app
from database import async_engine, BackgroundTask, TaskStatus, PracticeSession
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

# Import analysis modules
from whisper_engine import transcribe
from grammar_corrector import get_corrected_grammar, get_speech_feedback, compare_answers
from language_analyzer import language_analyzer

logger = logging.getLogger(__name__)

async def update_task_status(task_id: str, status: TaskStatus, progress: int = 0, status_message: Optional[str] = None, result: Optional[Dict] = None, error: Optional[str] = None):
    """Update background task status in database"""
    try:
        async with AsyncSession(async_engine) as session:
            statement = select(BackgroundTask).where(BackgroundTask.task_id == task_id)
            result_obj = await session.exec(statement)
            task = result_obj.first()
            
            if task:
                task.status = status
                task.progress = progress
                if status_message: # Update status message if provided
                    task.status_message = status_message
                task.updated_at = datetime.now(timezone.utc) # Update timestamp

                if result:
                    task.result = json.dumps(result)
                    task.status_message = "Evaluation complete. Results ready."
                if error:
                    task.error_message = error
                    task.status_message = f"Task failed: {error}"
                
                if status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                    task.completed_at = datetime.now(timezone.utc)
                
                session.add(task)
                await session.commit()
                
    except Exception as e:
        logger.error(f"Error updating task status for {task_id}: {e}")

@celery_app.task(bind=True)
def evaluate_speech_background(
    self,
    audio_file_path: str,
    question: str,
    ideal_answer: str,
    difficulty: str,
    user_id: int,
    model: str = "mistral:latest"
):
    """Background task for comprehensive speech evaluation"""
    task_id = self.request.id
    
    async def _evaluate():
        try:
            # Update status to processing
            await update_task_status(task_id, TaskStatus.PROCESSING, 10, status_message="Initializing evaluation...")
            
            # Step 1: Transcribe audio
            logger.info(f"Starting transcription for task {task_id}")
            await update_task_status(task_id, TaskStatus.PROCESSING, 20, status_message="Transcribing audio...")
            transcript, flagged_words = transcribe(audio_file_path)
            
            if not transcript:
                await update_task_status(task_id, TaskStatus.FAILED, 0, status_message="Transcription failed: No speech detected.", error="No speech detected in audio")
                return {"error": "No speech detected in audio"}
            
            await update_task_status(task_id, TaskStatus.PROCESSING, 30, status_message="Audio transcribed. Analyzing grammar...")
            
            # Step 2: Grammar analysis
            logger.info(f"Analyzing grammar for task {task_id}")
            grammar_output = get_corrected_grammar(transcript, question=question, model=model)
            await update_task_status(task_id, TaskStatus.PROCESSING, 50, status_message="Grammar analyzed. Assessing pronunciation...")
            
            # Step 3: Pronunciation feedback
            logger.info(f"Analyzing pronunciation for task {task_id}")
            feedback_output = get_speech_feedback(flagged_words, transcript=transcript, question=question, model=model)
            await update_task_status(task_id, TaskStatus.PROCESSING, 60, status_message="Pronunciation assessed. Evaluating content...")
            
            # Step 4: Content evaluation
            logger.info(f"Comparing answers for task {task_id}")
            comparison_output = compare_answers(transcript, ideal_answer, model=model)
            await update_task_status(task_id, TaskStatus.PROCESSING, 70, status_message="Content evaluated. Performing advanced analysis...")
            
            # Step 5: Advanced language analysis
            logger.info(f"Performing advanced language analysis for task {task_id}")
            
            # Get audio duration for speaking rate calculation
            try:
                import librosa
                y, sr = librosa.load(audio_file_path, sr=None)
                audio_duration = len(y) / sr
            except Exception as e:
                logger.warning(f"Could not get audio duration: {e}")
                audio_duration = None
            
            # Comprehensive language analysis
            language_analysis_results = await language_analyzer.comprehensive_analysis(
                text=transcript,
                audio_path=audio_file_path,
                audio_duration=audio_duration
            )
            
            await update_task_status(task_id, TaskStatus.PROCESSING, 85, status_message="Advanced analysis complete. Calculating rating...")
            
            # Step 6: Calculate rating
            from main import calculate_rating
            rating = calculate_rating(transcript, grammar_output, feedback_output, comparison_output)
            
            # Step 7: Save to database
            logger.info(f"Saving results to database for task {task_id}")
            async with AsyncSession(async_engine) as session:
                # Create practice session
                from database import PracticeSessionCreate
                practice_session_data = PracticeSessionCreate(
                    topic=question,
                    difficulty=difficulty,
                    question=question,
                    transcript=transcript,
                    grammar_feedback=grammar_output,
                    pronunciation_feedback=feedback_output,
                    content_evaluation=comparison_output,
                    rating=rating,
                    user_id=user_id
                )
                
                db_practice_session = PracticeSession.from_orm(practice_session_data)
                session.add(db_practice_session)
                await session.commit()
                await session.refresh(db_practice_session)
                
                # Save advanced language analysis
                if language_analysis_results:
                    pass
            
            # Prepare final result
            result = {
                "practice_session_id": db_practice_session.id,
                "transcript": transcript,
                "grammar_feedback": grammar_output,
                "pronunciation_feedback": feedback_output,
                "content_evaluation": comparison_output,
                "rating": rating,
                "language_analysis": language_analysis_results
            }
            
            await update_task_status(task_id, TaskStatus.COMPLETED, 100, status_message="Evaluation complete. Results ready.", result=result)
            logger.info(f"Task {task_id} completed successfully")
            
            return result
            
        except Exception as e:
            error_msg = f"Error in speech evaluation: {str(e)}"
            logger.error(f"Task {task_id} failed: {error_msg}")
            await update_task_status(task_id, TaskStatus.FAILED, 0, status_message=f"Evaluation failed: {error_msg}", error=error_msg)
            return {"error": error_msg}
        
        finally:
            # Clean up temporary audio file
            try:
                if os.path.exists(audio_file_path):
                    os.remove(audio_file_path)
            except Exception as e:
                logger.warning(f"Could not remove temporary file {audio_file_path}: {e}")
    
    # Run the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_evaluate())
    finally:
        loop.close()

@celery_app.task(bind=True)
def analyze_language_background(self, text: str, audio_path: Optional[str] = None):
    """Background task for advanced language analysis only"""
    task_id = self.request.id
    
    async def _analyze():
        try:
            await update_task_status(task_id, TaskStatus.PROCESSING, 20)
            
            # Get audio duration if audio path provided
            audio_duration = None
            if audio_path and os.path.exists(audio_path):
                try:
                    import librosa
                    y, sr = librosa.load(audio_path, sr=None)
                    audio_duration = len(y) / sr
                except Exception as e:
                    logger.warning(f"Could not get audio duration: {e}")
            
            await update_task_status(task_id, TaskStatus.PROCESSING, 50)
            
            # Perform comprehensive analysis
            results = await language_analyzer.comprehensive_analysis(
                text=text,
                audio_path=audio_path,
                audio_duration=audio_duration
            )
            
            await update_task_status(task_id, TaskStatus.COMPLETED, 100, results)
            return results
            
        except Exception as e:
            error_msg = f"Error in language analysis: {str(e)}"
            logger.error(f"Task {task_id} failed: {error_msg}")
            await update_task_status(task_id, TaskStatus.FAILED, 0, error=error_msg)
            return {"error": error_msg}
        
        finally:
            # Clean up temporary audio file if provided
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except Exception as e:
                    logger.warning(f"Could not remove temporary file {audio_path}: {e}")
    
    # Run the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_analyze())
    finally:
        loop.close()

@celery_app.task
def cleanup_old_tasks():
    """Periodic task to clean up old completed/failed tasks"""
    async def _cleanup():
        try:
            from datetime import datetime, timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=7)  # Keep tasks for 7 days
            
            async with AsyncSession(async_engine) as session:
                statement = select(BackgroundTask).where(
                    BackgroundTask.created_at < cutoff_date,
                    BackgroundTask.status.in_([TaskStatus.COMPLETED, TaskStatus.FAILED])
                )
                result = await session.exec(statement)
                old_tasks = result.all()
                
                for task in old_tasks:
                    await session.delete(task)
                
                await session.commit()
                logger.info(f"Cleaned up {len(old_tasks)} old tasks")
                
        except Exception as e:
            logger.error(f"Error cleaning up old tasks: {e}")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_cleanup())
    finally:
        loop.close()