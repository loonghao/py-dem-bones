#!/bin/bash
# macOS 平台安装 Eigen 库

set -e  # 遇到错误立即退出

# 检查是否已安装
if [ -d "extern/eigen/Eigen" ]; then
  echo "Eigen 库已安装，跳过安装步骤..."
  exit 0
fi

echo "开始安装 Eigen 库..."

# 创建目录
mkdir -p extern/eigen

# 检查 brew 是否已安装 eigen
if brew list eigen &>/dev/null; then
  echo "Eigen 已通过 brew 安装，使用现有安装..."
else
  # 使用重试脚本安装 Eigen
  echo "通过 brew 安装 Eigen（带重试机制）..."
  # 确保重试脚本有执行权限
  chmod +x .github/scripts/mac/retry_command.sh
  
  # 使用重试脚本执行 brew 安装命令，最多重试 3 次，初始延迟 5 秒
  .github/scripts/mac/retry_command.sh 3 5 brew install --quiet eigen
fi

# 获取 Eigen 路径并创建符号链接
EIGEN_PATH=$(brew --prefix eigen)
ln -sf $EIGEN_PATH/include/eigen3/Eigen extern/eigen/Eigen

# 验证安装
if [ -d "extern/eigen/Eigen" ]; then
  echo "Eigen 库已成功安装并链接，路径: $EIGEN_PATH"
else
  echo "Eigen 库安装失败"
  exit 1
fi
