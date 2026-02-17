#!/bin/bash
set -e

# Create venv if not exists
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install deps in venv
pip install -r requirements_minimal.txt

# Start backend server
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
