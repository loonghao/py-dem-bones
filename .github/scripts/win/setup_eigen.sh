#!/bin/bash
# Windows 平台安装 Eigen 库

# 创建目录
mkdir -p extern/eigen

# 直接下载 Eigen 库 zip 文件
curl -L -o eigen.zip https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.zip

# 解压并复制 Eigen 目录
unzip -q eigen.zip
cp -r eigen-3.4.0/Eigen extern/eigen/

# 清理临时文件
rm -rf eigen.zip eigen-3.4.0

echo "Eigen 库已成功安装到 extern/eigen 目录"
