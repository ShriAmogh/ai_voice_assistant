#!/bin/bash

echo "Stopping any existing processes on ports 3001 and 8001..."
kill -9 $(lsof -t -i:3001) 2>/dev/null || true
kill -9 $(lsof -t -i:8001) 2>/dev/null || true

echo "Starting Backend (Port 8001)..."
cd backend
# Check if virtual environment exists and activate it
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi
python main.py &
BACKEND_PID=$!
cd ..

echo "Starting Frontend (Port 3001)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "====================================================="
echo "✅ AI Voice Assistant is running!"
echo "➡️  Frontend: http://localhost:3001"
echo "➡️  Backend: http://localhost:8001"
echo "Press Ctrl+C to stop both services."
echo "====================================================="

# Trap Ctrl+C (SIGINT) and kill the child processes
trap "echo 'Stopping services...'; kill -9 $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM

# Wait for background processes
wait $BACKEND_PID $FRONTEND_PID
