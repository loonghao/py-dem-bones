#!/bin/bash
# Windows 平台安装 Eigen 库

# 直接克隆 Eigen 仓库
mkdir -p extern/eigen
git clone --depth 1 https://gitlab.com/libeigen/eigen.git extern/eigen

echo "Eigen 库已成功克隆到 extern/eigen 目录"
