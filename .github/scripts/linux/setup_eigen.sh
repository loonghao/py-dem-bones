#!/bin/bash
# Linux 平台安装 Eigen 库

# 安装 Eigen 库
sudo apt-get update
sudo apt-get install -y libeigen3-dev

# 创建符号链接
mkdir -p extern/eigen
sudo ln -sf /usr/include/eigen3/Eigen extern/eigen/Eigen

echo "Eigen 库已成功安装并链接"
