@echo off
title Samantha - Emotional Companion
echo [1/3] Installing Python dependencies...
pip install -r requirements.txt --quiet
echo [2/3] Installing frontend dependencies...
cd frontend && call npm install && cd ..
echo [3/3] Starting backend + frontend...
start "Samantha Backend" cmd /k "python server.py"
start "Samantha Frontend" cmd /k "cd frontend && npm run dev"
echo --------------------------------------
echo Backend:  http://127.0.0.1:8000
echo Frontend: http://localhost:3000
echo --------------------------------------
pause
