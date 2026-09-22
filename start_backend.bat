@echo off
chcp 65001 >nul
title 智面舱 - 后端 API 服务 (Port: 8000)
echo 正在启动后端 FastAPI 服务 (http://127.0.0.1:8000)...
cd /d "%~dp0backend"
"%~dp0.venv\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
pause
