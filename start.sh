#!/bin/bash

# 设置虚拟环境目录
VENV_DIR=".venv"
BACKEND_DIR="backend"
FRONTEND_DIR="frontend"

# 检查 Python 环境
if command -v python3 &>/dev/null; then
    PYTHON_CMD=python3
elif command -v python &>/dev/null; then
    PYTHON_CMD=python
else
    echo "错误: 未找到 Python。请安装 Python 3.x"
    exit 1
fi

# 检查 Node.js 环境
if ! command -v npm &>/dev/null; then
    echo "错误: 未找到 npm。请安装 Node.js"
    exit 1
fi

# 检查 uv 是否已安装
if ! command -v uv &>/dev/null; then
    echo "正在安装 uv 包管理器..."
    $PYTHON_CMD -m pip install uv
fi

# 创建并激活虚拟环境
echo "设置 Python 虚拟环境..."
if [ ! -d "$VENV_DIR" ]; then
    echo "创建新的虚拟环境..."
    uv venv $VENV_DIR  --python 3.11
fi

# 根据操作系统确定激活脚本
if [ "$(uname)" = "Darwin" ] || [ "$(uname)" = "Linux" ]; then
    # macOS 或 Linux
    source "$VENV_DIR/bin/activate"
else
    # Windows with Git Bash or similar
    source "$VENV_DIR/Scripts/activate"
fi

# 安装 Python 依赖
echo "安装 Python 依赖..."
cd $BACKEND_DIR
uv pip install -r requirements.txt
cd ..

# 安装 Node.js 依赖
echo "安装 Node.js 依赖..."
cd $FRONTEND_DIR
npm install
cd ..

# 修改 Python 服务路径
echo "配置 Python 服务路径..."
PYTHON_PATH="$(pwd)/$VENV_DIR/bin/python"
if [ ! -f "$PYTHON_PATH" ]; then
    # 可能是 Windows 路径
    PYTHON_PATH="$(pwd)/$VENV_DIR/Scripts/python"
fi

# 导出环境变量，让 Electron 知道 Python 解释器的位置
export ASR_PYTHON_PATH="$PYTHON_PATH"

# 安装 FFmpeg
echo "正在设置 FFmpeg..."
python scripts/setup_ffmpeg.py
if [ $? -ne 0 ]; then
    echo "FFmpeg 设置失败"
    exit 1
fi

# 启动应用
echo "启动应用..."
cd $FRONTEND_DIR
npm run electron:dev
