#!/bin/bash
# macOS 平台安装 Eigen 库

# 安装 Eigen 库
brew install eigen

# 创建符号链接
mkdir -p extern/eigen
EIGEN_PATH=$(brew --prefix eigen)
ln -sf $EIGEN_PATH/include/eigen3/Eigen extern/eigen/Eigen

echo "Eigen 库已成功安装并链接，路径: $EIGEN_PATH"
