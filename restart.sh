#!/bin/bash

# Stop any running instances
echo "Stopping any running instances..."
pkill -f "python run.py" || echo "No running instances found"

# Activate virtual environment and start application
echo "Starting application..."
source venv/bin/activate && python run.py 