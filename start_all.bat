@echo off
chcp 65001 >nul
title 智面舱 AI Interview Hub 一键启动
echo ===================================================
echo   《智面舱 AI Interview Hub》一键启动服务
echo ===================================================
echo.
echo [1/2] 正在启动后端服务 (FastAPI, 端口 8000)...
start "智面舱 - 后端 API 服务 (Port: 8000)" cmd /k "cd /d "%~dp0backend" && "%~dp0.venv\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

echo [2/2] 正在启动前端服务 (Vite, 端口 5173)...
start "智面舱 - 前端 Vite 服务 (Port: 5173)" cmd /k "cd /d "%~dp0frontend" && npm.cmd run dev"

echo.
echo ===================================================
echo   服务已启动完成！
echo.
echo   - 前端访问地址: http://localhost:5173
echo   - 后端 Swagger 接口文档: http://127.0.0.1:8000/docs
echo.
echo   【内置演示账号（密码统一为 123456）】:
echo   - 个人求职者: student@example.com (张同学)
echo   - 企业招聘官: hr@example.com (华为 HR)
echo   - 企业管理员: admin_corp@example.com
echo   - 平台管理员: admin@example.com
echo ===================================================
echo.
pause
