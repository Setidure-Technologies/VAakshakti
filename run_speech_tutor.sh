#!/bin/bash

# Move into the app directory (edit as needed)
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Create logs directory if missing
mkdir -p logs

# Start app in background with nohup
nohup python app.py > logs/app_output.log 2>&1 &

# Print status
echo "✅ Speech Tutor is now running in the background!"
echo "📄 Logs are being written to logs/app_output.log"
echo "🌐 Visit: http://localhost:7777"
