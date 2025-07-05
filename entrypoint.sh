#!/bin/sh
set -e

if [ "$1" = "celery" ]; then
  exec celery -A celery_app.celery_app worker -l info -Q celery,transcription,audio_processing,text_analysis,llm_feedback,notifications,speech_evaluation,language_analysis --concurrency=2
elif [ "$1" = "uvicorn" ]; then
  exec uvicorn main:app --host 0.0.0.0 --port 1212
else
  exec "$@"
fi