#!/bin/bash

# AI 剧本评测系统 - Web 服务启动脚本

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 解析命令行参数
DAEMON_MODE=false
for arg in "$@"; do
  case $arg in
    -d|--daemon|--background)
      DAEMON_MODE=true
      shift
      ;;
    -h|--help)
      echo "用法: $0 [选项]"
      echo ""
      echo "选项:"
      echo "  -d, --daemon, --background    后台模式运行（默认前台模式）"
      echo "  -h, --help                   显示此帮助信息"
      echo ""
      echo "前台模式: 日志实时显示在当前终端，Ctrl+C 停止服务"
      echo "后台模式: 服务在后台运行，使用 ./logs.sh 查看日志"
      exit 0
      ;;
  esac
done

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

# 清理被占用的端口（非系统进程）
echo "🧹 清理被占用的端口..."
PORTS_CLEANED=0
for port in 5000 5001 5002 8000 8001 8080 3000; do
  pid=$(lsof -ti:$port 2>/dev/null || true)
  if [ -n "$pid" ]; then
    # 检查是否是 Python app.py 进程（添加错误处理）
    cmd=$(ps -p $pid -o command= 2>/dev/null | tail -1) || cmd=""
    if [[ "$cmd" == *"python"*app.py* ]] || [[ "$cmd" == *"Python"*app.py* ]] || [[ "$cmd" == *"/app.py"* ]]; then
      echo "  • 清理端口 $port (进程 $pid: $cmd)"
      kill -9 $pid 2>/dev/null || true
      PORTS_CLEANED=$((PORTS_CLEANED + 1))
    fi
  fi
done

if [ $PORTS_CLEANED -gt 0 ]; then
  echo "  ✅ 已清理 $PORTS_CLEANED 个被占用的端口"
  sleep 1
else
  echo "  ℹ️  端口未被占用"
fi
echo

if [ "$DAEMON_MODE" = true ]; then
  # ==================== 后台模式 ====================
  echo "📋 模式: 后台运行"
  echo ""

  # 启动 Flask 应用（会自动查找可用端口）
  echo "⏳ 启动服务器..."
  nohup python3 app.py > /tmp/app_startup.log 2>&1 &
  SERVER_PID=$!

  echo "📝 服务器 PID: $SERVER_PID"
  echo "📋 启动日志: /tmp/app_startup.log"

  # 等待服务器启动
  echo "⌛ 等待服务器启动..."
  sleep 5

  # 检查进程是否还在运行
  if ! ps -p $SERVER_PID >/dev/null 2>&1; then
    echo "❌ 服务器启动失败！请查看日志: /tmp/app_startup.log"
    cat /tmp/app_startup.log
    exit 1
  fi

  # 直接通过 PID 查找服务器实际监听的端口（最准确的方法）
  echo "🔍 检测服务端口..."
  ACTUAL_PORT=""
  if ps -p $SERVER_PID >/dev/null 2>&1; then
    # 从 lsof 查找该进程监听的所有端口（IPv4 + TCP + LISTEN）
    # 使用 tail -n +2 跳过表头，防止提取到 "NAME" 字段名
    ACTUAL_PORT=$(lsof -Pan -p $SERVER_PID -i 2>/dev/null | tail -n +2 | grep -i listen | awk '{print $9}' | cut -d':' -f2 | head -1)

    if [ -n "$ACTUAL_PORT" ] && [[ "$ACTUAL_PORT" =~ ^[0-9]+$ ]]; then
      echo "✅ 找到服务运行在端口: $ACTUAL_PORT (PID: $SERVER_PID)"
    else
      echo "⚠️  无法通过 lsof 检测端口，尝试读取启动日志..."
      # 备选方法：从 app.py 的输出中读取端口
      ACTUAL_PORT=$(grep -oP '访问地址: http://localhost:\K\d+' /tmp/app_startup.log 2>/dev/null | head -1)
      if [ -n "$ACTUAL_PORT" ]; then
        echo "✅ 从日志找到服务运行在端口: $ACTUAL_PORT"
      fi
    fi
  else
    echo "❌ 无法检测到运行中的服务器进程"
  fi

  # 显示访问地址
  if [ -n "$ACTUAL_PORT" ]; then
    echo ""
    echo "=========================================="
    echo "  🎉 服务启动成功！"
    echo "=========================================="
    echo ""
    echo "📍 访问地址："
    echo ""
    echo "  🖥️  前端界面（Web）："
    echo "     本地访问: http://localhost:$ACTUAL_PORT"
    echo "     局域网: http://$(ipconfig getifaddr en0 2>/dev/null || echo '192.168.1.133'):$ACTUAL_PORT"
    echo ""
    echo "  🔌 后端API："
    echo "     API根路径: http://localhost:$ACTUAL_PORT/api"
    echo "     评测接口: http://localhost:$ACTUAL_PORT/api/evaluate"
    echo "     历史记录: http://localhost:$ACTUAL_PORT/api/history"
    echo ""
    echo "=========================================="
    echo ""
    echo "✅ 服务已在后台运行 (PID: $SERVER_PID)"
    echo ""
    echo "📺 查看日志命令："
    echo "   ./logs.sh              实时查看所有日志"
    echo "   ./logs.sh filter       实时查看关键日志（推荐）"
    echo "   ./logs.sh recent 100   查看最近100行"
    echo "   ./logs.sh errors       查看错误日志"
    echo ""
    echo "🛑 停止服务: kill $SERVER_PID"
    echo "            或: pkill -f 'python.*app.py'"
    echo ""
  fi

  # 脚本结束，服务在后台运行
  echo "🚀 启动完成！"
  echo ""
  echo "💡 提示: 使用 './logs.sh filter' 实时查看评测日志"
  echo ""

else
  # ==================== 前台模式（默认）====================
  echo "📋 模式: 前台运行（日志实时显示）"
  echo ""
  echo "💡 提示: 按 Ctrl+C 停止服务"
  echo ""
  echo "=========================================="
  echo "  🚀 启动服务中..."
  echo "=========================================="
  echo ""

  # 直接运行，日志输出到当前终端
  exec python3 app.py
fi
