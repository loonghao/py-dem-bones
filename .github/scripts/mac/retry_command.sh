#!/bin/bash
# macOS 平台命令重试脚本

# 参数说明
# $1: 最大重试次数
# $2: 初始重试延迟（秒）
# $3 及以后: 要执行的命令及其参数

# 检查参数
if [ $# -lt 3 ]; then
  echo "用法: $0 <最大重试次数> <初始重试延迟> <命令...>"
  exit 1
fi

MAX_RETRIES=$1
RETRY_DELAY=$2
shift 2  # 移除前两个参数，剩下的是要执行的命令

# 执行命令并在失败时重试
attempt=0
while [ $attempt -lt $MAX_RETRIES ]; do
  if [ $attempt -gt 0 ]; then
    echo "重试尝试 $attempt/$MAX_RETRIES: $@"
  fi
  
  # 执行命令
  "$@"
  exit_code=$?
  
  # 检查命令是否成功
  if [ $exit_code -eq 0 ]; then
    # 命令成功，退出循环
    if [ $attempt -gt 0 ]; then
      echo "命令在第 $attempt 次尝试后成功执行"
    fi
    exit 0
  else
    # 命令失败
    attempt=$((attempt + 1))
    if [ $attempt -lt $MAX_RETRIES ]; then
      echo "命令失败，退出代码: $exit_code"
      echo "等待 $RETRY_DELAY 秒后重试..."
      sleep $RETRY_DELAY
      # 指数退避策略
      RETRY_DELAY=$((RETRY_DELAY * 2))
    else
      echo "命令在 $MAX_RETRIES 次尝试后仍然失败"
      exit $exit_code
    fi
  fi
done
