#!/bin/bash
# Python 3.7 环境设置脚本

# 安装基础依赖
python -m pip install --upgrade pip
python -m pip install pipx
pipx install nox
python -m pip install pytest pytest-cov

# 安装兼容 Python 3.7 的依赖版本
python -m pip install -e ".[dev]"
python -m pip install "isort<5.12.0"
python -m pip install "black<23.0.0"
python -m pip install "ruff<0.1.0"
python -m pip install mypy

echo "Python 3.7 环境已设置完成"
