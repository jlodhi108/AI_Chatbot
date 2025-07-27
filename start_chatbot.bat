@echo off
echo Starting AI Girlfriend Chatbot System...
echo.

echo Starting Backend Server...
start "Backend Server" cmd /k "cd /d %~dp0 && python backend.py"

echo Waiting 5 seconds for backend to start...
timeout /t 5 /nobreak >nul

echo Starting Frontend...
start "Frontend" cmd /k "cd /d %~dp0 && streamlit run frontend.py"

echo.
echo Both servers are starting up!
echo Backend will be available at: http://127.0.0.1:9999
echo Frontend will be available at: http://localhost:8501
echo.
pause
