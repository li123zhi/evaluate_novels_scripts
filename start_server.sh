#!/bin/bash
# AI 剧本评测系统启动脚本

echo "================================"
echo "🚀 启动 AI 剧本评测系统"
echo "================================"
echo ""

# 检查是否已有运行的进程
if pgrep -f "python.*app.py" > /dev/null; then
    echo "⚠️  检测到已有服务器在运行，正在停止..."
    pkill -f "python.*app.py"
    sleep 2
    echo "✅ 旧服务器已停止"
    echo ""
fi

# 启动新服务器
echo "📍 启动服务器..."
python app.py

# 如果服务器意外退出，暂停一下以便查看错误信息
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ 服务器启动失败！"
    echo "请检查错误信息"
    read -p "按任意键退出..."
fi
