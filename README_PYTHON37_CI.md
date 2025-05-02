# Python 3.7 CI 配置指南

本文档提供了关于如何在 GitHub Actions 中配置 Python 3.7 环境的指南，特别是针对 DCC（数字内容创建）工具场景。

## 背景

Python 3.7 已于 2023 年 6 月 27 日达到生命周期结束 (EOL)，GitHub Actions 已经开始从其最新的运行器镜像中移除 Python 3.7 支持。这导致使用 `actions/setup-python@v5` 安装 Python 3.7 时可能会失败，特别是在最新的 Ubuntu 运行器上。

## 解决方案

我们实施了两个工作流文件来解决这个问题：

1. **python37_ci.yml**: 使用多种方法在 Windows、macOS 和 Linux 上构建和测试包
2. **python37_dcc_test.yml**: 在模拟的 DCC 环境（如 Blender 和 Maya）中测试包

### 主要策略

我们使用了以下策略来确保 Python 3.7 兼容性：

1. **使用 Docker 容器**：在 Linux 上，我们使用官方的 Python 3.7 Docker 镜像
2. **使用较旧的运行器版本**：
   - Windows: `windows-2019`
   - macOS: `macos-11`
   - Ubuntu: `ubuntu-20.04`
3. **使用 uv/uvx**：作为备选方案，我们使用 uv 创建临时 Python 3.7 环境
4. **模拟 DCC 环境**：我们创建了模拟 Blender 和 Maya 环境的测试

## 工作流详解

### python37_ci.yml

这个工作流包含四个主要作业：

1. **build-linux**：使用 Python 3.7 Docker 容器在 Linux 上构建
2. **build-windows**：在 Windows 2019 上使用 actions/setup-python@v4 安装 Python 3.7
3. **build-macos**：在 macOS 11 上使用 actions/setup-python@v4 安装 Python 3.7
4. **build-with-uv**：使用 uv 在所有平台上创建 Python 3.7 环境

所有作业都会构建包并上传 wheel 文件作为构件。最后，`combine-wheels` 作业会收集所有平台的 wheel 文件。

### python37_dcc_test.yml

这个工作流模拟 DCC 环境进行测试：

1. **test-blender**：下载 Blender 2.93（使用 Python 3.7）并在其 Python 环境中测试包
2. **test-maya**：模拟 Maya 的 Python 环境并测试包

## 使用说明

### 运行 CI

可以通过以下方式手动触发工作流：

1. 在 GitHub 仓库页面上，点击 "Actions" 标签
2. 选择 "Python 3.7 CI for DCC" 或 "Python 3.7 DCC Environment Tests" 工作流
3. 点击 "Run workflow" 按钮
4. 选择分支并点击 "Run workflow"

### 查看结果

构建完成后，可以在工作流运行页面上下载构建的 wheel 文件：

1. 点击完成的工作流运行
2. 滚动到页面底部的 "Artifacts" 部分
3. 下载 "py-dem-bones-all-platforms-py37" 构件，其中包含所有平台的 wheel 文件

## 注意事项

1. **长期解决方案**：考虑将项目升级到 Python 3.8 或更高版本，因为 Python 3.7 已经 EOL
2. **Docker 限制**：Docker 容器方法在 Windows 和 macOS 上有限制，因此我们在这些平台上使用其他方法
3. **DCC 兼容性**：如果您的 DCC 工具仍然使用 Python 3.7，这些工作流可以确保兼容性

## 故障排除

如果工作流失败，请检查以下几点：

1. **Python 版本问题**：确保使用 `actions/setup-python@v4` 而不是 `v5` 来安装 Python 3.7
2. **运行器版本**：如果在较新的运行器上失败，尝试使用较旧的运行器版本
3. **Docker 问题**：检查 Docker 容器是否可用，或者尝试使用 uv 方法
4. **DCC 特定问题**：检查 DCC 工具的 Python 环境要求
