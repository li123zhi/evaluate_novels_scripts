#!/bin/bash

# AI 剧本评测系统 - Web 服务启动脚本

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================"
echo "  AI 剧本评测系统 - Web 服务"
echo "================================"
echo

# 检查 Python 是否安装（优先使用 Python 3.13+）
PYTHON_CMD=""

if command -v python3.13 &> /dev/null; then
    PYTHON_CMD="python3.13"
elif command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
elif command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo "❌ 错误: 未找到 Python 3"
    echo "   请先安装 Python 3.13 或更高版本"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version)
echo "✅ Python 版本: $PYTHON_VERSION"

# 检查虚拟环境的 Python 版本是否匹配
if [ -d "venv" ]; then
    VENV_PYTHON_VERSION=$(venv/bin/python --version 2>&1 | awk '{print $2}')
    echo "📦 虚拟环境 Python 版本: $VENV_PYTHON_VERSION"

    # 如果虚拟环境版本不是 3.13+，询问是否重建
    if [[ ! "$VENV_PYTHON_VERSION" =~ 3\.(1[3-9]|[2-9][0-9]) ]]; then
        echo
        echo "⚠️  虚拟环境使用的是旧版本 Python ($VENV_PYTHON_VERSION)"
        echo "   建议使用 Python 3.13+ 以获得更好的性能"
        echo
        read -p "是否删除旧虚拟环境并重新创建? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "🗑️  删除旧虚拟环境..."
            rm -rf venv
            echo
            echo "📦 使用 Python 3.13+ 创建虚拟环境..."
            $PYTHON_CMD -m venv venv
            echo "✅ 虚拟环境创建完成"
        fi
    fi
fi

# 检查是否存在虚拟环境
if [ ! -d "venv" ]; then
    echo
    echo "📦 虚拟环境不存在，正在创建..."
    $PYTHON_CMD -m venv venv
    echo "✅ 虚拟环境创建完成"
fi

# 激活虚拟环境
echo
echo "🔄 激活虚拟环境..."
source venv/bin/activate

# 检查并安装依赖
echo
echo "📥 检查依赖..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✅ 依赖检查完成"

# 检查配置文件
if [ ! -f ".env" ]; then
    echo
    echo "⚠️  警告: .env 文件不存在"
    echo "   正在从 .env.example 复制..."
    cp .env.example .env
    echo "📝 请编辑 .env 文件，填入你的 API 配置"
    echo
    echo "   需要配置的变量:"
    echo "   - ARK_API_KEY"
    echo "   - ARK_BASE_URL"
    echo "   - MODEL_ENDPOINT"
    echo
    read -p "按 Enter 继续，或按 Ctrl+C 退出进行配置..."
fi

# 检查配置
echo
echo "🔍 检查配置..."
python main.py check-config

echo
echo "================================"
echo "  启动 Web 服务"
echo "================================"
echo

# 启动 Flask 应用（会自动查找可用端口）
python app.py
