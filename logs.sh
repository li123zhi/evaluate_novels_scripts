#!/bin/bash
# 实时查看评测日志

case "$1" in
  "all"|"")
    echo "📺 实时查看所有日志（按 Ctrl+C 停止）..."
    echo ""
    tail -f /tmp/app_startup.log
    ;;
  "filter"|"grep")
    echo "📺 实时查看关键日志（按 Ctrl+C 停止）..."
    echo ""
    tail -f /tmp/app_startup.log | grep --line-buffered -E "INFO|ERROR|评测|维度|得分|API|📊|✅|❌"
    ;;
  "recent"|"last")
    LINES=${2:-50}
    echo "📋 查看最近 ${LINES} 行日志："
    echo ""
    tail -${LINES} /tmp/app_startup.log
    ;;
  "errors"|"error")
    echo "❌ 查看错误日志："
    echo ""
    grep -E "ERROR|Exception|Failed|failed" /tmp/app_startup.log | tail -50
    ;;
  "help"|"-h"|"--help")
    cat << EOF
📺 日志查看工具

用法:
  ./logs.sh [命令] [参数]

命令:
  all (默认)      实时查看所有日志
  filter, grep    实时查看关键日志（过滤INFO/ERROR/评测/维度等）
  recent, last    查看最近N行日志（默认50行）
  errors, error   查看错误日志
  help            显示此帮助信息

示例:
  ./logs.sh              # 实时查看所有日志
  ./logs.sh filter       # 实时查看关键日志
  ./logs.sh recent 100   # 查看最近100行
  ./logs.sh errors       # 查看错误日志

注意: 实时查看时按 Ctrl+C 停止
EOF
    ;;
  *)
    echo "❌ 未知命令: $1"
    echo "使用 './logs.sh help' 查看帮助"
    exit 1
    ;;
esac
