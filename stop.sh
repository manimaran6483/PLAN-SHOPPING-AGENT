#!/bin/bash

# Stop script for Insurance Plan AI Assistant API

echo "Stopping Insurance Plan AI Assistant API..."

# Find and kill the FastAPI process
PID=$(ps aux | grep '[p]ython main.py' | awk '{print $2}')

if [ -z "$PID" ]; then
    echo "No running FastAPI server found on main.py"
    
    # Also check for uvicorn processes
    UVICORN_PID=$(ps aux | grep '[u]vicorn.*main:app' | awk '{print $2}')
    
    if [ -z "$UVICORN_PID" ]; then
        echo "No uvicorn processes found either."
        echo "Server may not be running."
    else
        echo "Found uvicorn process with PID: $UVICORN_PID"
        echo "Stopping uvicorn process..."
        kill -TERM $UVICORN_PID
        
        # Wait a few seconds for graceful shutdown
        sleep 3
        
        # Check if process is still running
        if kill -0 $UVICORN_PID 2>/dev/null; then
            echo "Process still running. Force killing..."
            kill -KILL $UVICORN_PID
        fi
        
        echo "Uvicorn server stopped successfully."
    fi
else
    echo "Found FastAPI server process with PID: $PID"
    echo "Stopping server..."
    
    # Send SIGTERM for graceful shutdown
    kill -TERM $PID
    
    # Wait a few seconds for graceful shutdown
    sleep 3
    
    # Check if process is still running
    if kill -0 $PID 2>/dev/null; then
        echo "Process still running. Force killing..."
        kill -KILL $PID
    fi
    
    echo "FastAPI server stopped successfully."
fi

# Also kill any remaining python processes that might be related
RELATED_PIDS=$(ps aux | grep -E '[p]ython.*8081|[p]ython.*fastapi|[p]ython.*uvicorn' | awk '{print $2}')

if [ ! -z "$RELATED_PIDS" ]; then
    echo "Found additional related processes: $RELATED_PIDS"
    echo "Stopping additional processes..."
    echo $RELATED_PIDS | xargs kill -TERM 2>/dev/null
    sleep 2
    echo $RELATED_PIDS | xargs kill -KILL 2>/dev/null
fi

echo "Cleanup completed."

# Optional: Deactivate virtual environment if it was activated
if [ ! -z "$VIRTUAL_ENV" ]; then
    echo "Deactivating virtual environment..."
    deactivate 2>/dev/null || true
fi

echo "Stop script finished."
