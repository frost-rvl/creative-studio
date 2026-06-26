#!/bin/bash

cd /root/creative-studio || exit 1

# Activate virtual environment (if using one)
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo " Virtual environment not found. Run: python3 -m venv .venv"
    exit 1
fi

# Stop any existing instance
pkill -f "npm run prod" 2>/dev/null
pkill -f "gunicorn" 2>/dev/null
pkill -f "pygbag" 2>/dev/null
pkill -f "python.*service" 2>/dev/null

# Start in the background with logging
nohup npm run prod > prod.log 2>&1 &

# Wait a moment and check if it's running
sleep 5
if pgrep -f "npm run prod" > /dev/null; then
    echo " npm run prod started in background (PID: $(pgrep -f 'npm run prod')). Log: prod.log"
else
    echo " Failed to start. Check prod.log"
    tail -20 prod.log
fi