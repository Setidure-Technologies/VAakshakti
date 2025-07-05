# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies that might be needed by some Python packages
# (e.g., for faster-whisper or other ML libraries if they have C extensions)
# This is a common set, adjust if needed.
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     ffmpeg \
#  && rm -rf /var/lib/apt/lists/*
# Note: ffmpeg might be needed for audio processing by whisper/pydub.
# If faster-whisper requires specific CUDA toolkit versions not in the base nvidia runtime,
# you might need a more specific base image like nvidia/cuda:X.Y-cudnnZ-runtime-ubuntuA.B

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# Using --no-cache-dir to reduce image size
# Adding a build arg to force re-run of this layer if needed for cache busting
ARG CACHEBUST=1
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK resources to a specific, accessible directory
ENV NLTK_DATA=/app/nltk_data
RUN python -m nltk.downloader -d $NLTK_DATA punkt

# Copy the rest of the application code into the container at /app
COPY main.py .
COPY llm_engine.py .
COPY whisper_engine.py .
COPY grammar_corrector.py .
COPY security.py .
COPY database.py .
COPY celery_app.py .
COPY tasks/ ./tasks/
COPY app/ ./app/
COPY language_analyzer.py .
COPY prompts/ ./prompts/
COPY entrypoint.sh .

# Make port 8000 available to the world outside this container
# This is the port Uvicorn will run on. We'll use 1212.
EXPOSE 1212

# Define environment variable (can be overridden by docker-compose)
ENV APP_MODULE="main:app"
ENV HOST="0.0.0.0"
ENV PORT="1212"

ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn"]
