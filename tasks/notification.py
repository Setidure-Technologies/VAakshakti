"""
Background tasks for notifications and reminders
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

from app.core.celery_instance import celery_app
from database import async_engine, BookingSlot, User, BookingStatus
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

logger = logging.getLogger(__name__)

@celery_app.task
def send_booking_reminder():
    """Send reminders for upcoming bookings"""
    
    async def _send_reminders():
        try:
            # Find bookings in the next 24 hours
            now = datetime.utcnow()
            reminder_time = now + timedelta(hours=24)
            
            async with AsyncSession(async_engine) as session:
                statement = select(BookingSlot, User).join(User).where(
                    BookingSlot.scheduled_time.between(now, reminder_time),
                    BookingSlot.status == BookingStatus.SCHEDULED
                )
                result = await session.exec(statement)
                bookings_with_users = result.all()
                
                for booking, user in bookings_with_users:
                    # Here you would integrate with email service, SMS, or push notifications
                    logger.info(f"Reminder: {user.email} has a {booking.session_type} session at {booking.scheduled_time}")
                    
                    # For now, just log the reminder
                    # In production, you'd send actual notifications
                    
        except Exception as e:
            logger.error(f"Error sending booking reminders: {e}")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_send_reminders())
    finally:
        loop.close()

@celery_app.task
def cleanup_expired_bookings():
    """Mark expired bookings as no-show"""
    
    async def _cleanup():
        try:
            now = datetime.utcnow()
            
            async with AsyncSession(async_engine) as session:
                # Find bookings that are past their scheduled time and still marked as scheduled
                statement = select(BookingSlot).where(
                    BookingSlot.scheduled_time < now,
                    BookingSlot.status == BookingStatus.SCHEDULED
                )
                result = await session.exec(statement)
                expired_bookings = result.all()
                
                for booking in expired_bookings:
                    booking.status = BookingStatus.NO_SHOW
                    booking.updated_at = now
                    session.add(booking)
                
                await session.commit()
                logger.info(f"Marked {len(expired_bookings)} bookings as no-show")
                
        except Exception as e:
            logger.error(f"Error cleaning up expired bookings: {e}")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_cleanup())
    finally:
        loop.close()

@celery_app.task
def generate_user_progress_report(user_id: int):
    """Generate a progress report for a user"""
    
    async def _generate_report():
        try:
            from database import PracticeSession
            
            async with AsyncSession(async_engine) as session:
                # Get user's practice sessions from last 30 days
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                
                statement = select(PracticeSession).where(
                    PracticeSession.user_id == user_id,
                    PracticeSession.timestamp >= thirty_days_ago
                ).order_by(PracticeSession.timestamp.desc())
                
                result = await session.exec(statement)
                sessions = result.all()
                
                if not sessions:
                    return {"message": "No practice sessions found in the last 30 days"}
                
                # Calculate progress metrics
                total_sessions = len(sessions)
                average_rating = sum(session.rating for session in sessions) / total_sessions
                
                # Group by difficulty
                difficulty_stats = {}
                for session in sessions:
                    diff = session.difficulty
                    if diff not in difficulty_stats:
                        difficulty_stats[diff] = {"count": 0, "avg_rating": 0, "ratings": []}
                    difficulty_stats[diff]["count"] += 1
                    difficulty_stats[diff]["ratings"].append(session.rating)
                
                for diff in difficulty_stats:
                    ratings = difficulty_stats[diff]["ratings"]
                    difficulty_stats[diff]["avg_rating"] = sum(ratings) / len(ratings)
                
                # Recent improvement trend
                recent_sessions = sessions[:10]  # Last 10 sessions
                older_sessions = sessions[10:20] if len(sessions) > 10 else []
                
                improvement_trend = "stable"
                if recent_sessions and older_sessions:
                    recent_avg = sum(s.rating for s in recent_sessions) / len(recent_sessions)
                    older_avg = sum(s.rating for s in older_sessions) / len(older_sessions)
                    
                    if recent_avg > older_avg + 0.2:
                        improvement_trend = "improving"
                    elif recent_avg < older_avg - 0.2:
                        improvement_trend = "declining"
                
                report = {
                    "user_id": user_id,
                    "period": "last_30_days",
                    "total_sessions": total_sessions,
                    "average_rating": round(average_rating, 2),
                    "difficulty_breakdown": difficulty_stats,
                    "improvement_trend": improvement_trend,
                    "generated_at": datetime.utcnow().isoformat()
                }
                
                logger.info(f"Generated progress report for user {user_id}")
                return report
                
        except Exception as e:
            logger.error(f"Error generating progress report for user {user_id}: {e}")
            return {"error": str(e)}
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_generate_report())
    finally:
        loop.close()

@celery_app.task
def send_booking_confirmation_notification_task(user_email: str, booking_details: dict):
    """
    Sends a booking confirmation notification.
    Placeholder: Logs the information.
    In a real app, this would use an email service.
    """
    try:
        logger.info(f"Sending booking confirmation to {user_email} for booking: {booking_details}")
        # Example:
        # subject = f"Booking Confirmation: {booking_details.get('session_type')} on {booking_details.get('scheduled_time')}"
        # body = f"Dear User,\n\nYour booking for a {booking_details.get('session_type')} session on {booking_details.get('scheduled_time')} is confirmed.\nTopic: {booking_details.get('topic', 'N/A')}\n\nThank you."
        # send_email_utility(user_email, subject, body)
        # For now, we just log.
        return {"status": "success", "message": f"Booking confirmation log generated for {user_email}."}
    except Exception as e:
        logger.error(f"Error in send_booking_confirmation_notification_task for {user_email}: {e}")
        # Optionally, re-raise or handle to allow retries if configured
        return {"status": "error", "message": str(e)}