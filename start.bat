@echo off
echo 启动 ASR GUI 应用...

REM 设置虚拟环境目录
set VENV_DIR=.venv
set BACKEND_DIR=backend
set FRONTEND_DIR=frontend

REM 检查 Python 环境
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo 错误: 未找到 Python。请安装 Python 3.x
    exit /b 1
)

REM 检查 Node.js 环境
where npm >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo 错误: 未找到 npm。请安装 Node.js
    exit /b 1
)

REM 检查 uv 是否已安装
where uv >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo 正在安装 uv 包管理器...
    python -m pip install uv
)

REM 创建虚拟环境
echo 设置 Python 虚拟环境...
if not exist %VENV_DIR% (
    echo 创建新的虚拟环境...
    call uv venv %VENV_DIR%
)

REM 激活虚拟环境
call %VENV_DIR%\Scripts\activate.bat

REM 安装 Python 依赖
echo 安装 Python 依赖...
cd %BACKEND_DIR%
call uv pip install -r requirements.txt
cd ..

REM 安装 Node.js 依赖
echo 安装 Node.js 依赖...
cd %FRONTEND_DIR%
call npm install
cd ..

REM 设置 Python 解释器路径
echo 配置 Python 服务路径...
set ASR_PYTHON_PATH=%CD%\%VENV_DIR%\Scripts\python.exe

REM 安装 FFmpeg
echo 正在设置 FFmpeg...
python scripts/setup_ffmpeg.py
if %ERRORLEVEL% NEQ 0 (
    echo FFmpeg 设置失败
    exit /b 1
)

REM 启动应用
echo 启动应用...
cd %FRONTEND_DIR%
call npm run electron:dev
