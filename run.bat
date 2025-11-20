@echo off
cd backend
call venv\Scripts\activate
start http://localhost:8000
uvicorn main:app --reload --port 8000
pause
