# GitHub Actions 工作流优化总结

## 优化目标

1. 确保文档和代码检查任务在 PR 时只执行一次
2. 在 PR 时测试所有 Python 版本
3. 在发布时只构建一次文档，然后构建所有 Python 版本并发布到 PyPI
4. 支持 Python 3.7 到 3.13 版本
5. 修复 Windows 环境中的构建问题
6. 简化工作流结构，提高可维护性

## 已完成的优化

### 1. 工作流结构优化

- **移除重复工作流**：删除了冗余的工作流文件，包括 `main-new.yml` 和平台特定的工作流目录
- **创建可重用工作流**：将常用任务定义移至 `reusable-jobs.yml`，实现代码复用
- **统一配置**：确保自动触发和手动触发的工作流使用相同的任务定义

### 2. 执行效率优化

- **单次执行任务**：
  - 代码检查任务仅在 Python 3.11 + Ubuntu 环境中执行一次
  - 文档构建任务仅在 Python 3.10 + Ubuntu 环境中执行一次
- **矩阵策略优化**：
  - 构建和测试任务使用矩阵策略覆盖所有平台和 Python 版本
  - 通过条件控制，避免在不必要的情况下执行任务

### 3. Python 版本支持

- **Python 3.7 支持**：
  - 添加专门的 Python 3.7 构建和测试任务
  - 使用 `actions/setup-python@v5` 显式安装 Python 3.7
- **Python 3.12 和 3.13 支持**：
  - 更新矩阵配置，添加 Python 3.12 和 3.13 版本
  - 确保所有任务兼容最新的 Python 版本

### 4. 命令执行优化

- **替换 `uvx` 命令**：
  - 使用 `python -m` 命令替代所有 `uvx` 命令
  - 构建：`python -m build` 替代 `uvx nox -s build`
  - 测试：`python -m pytest` 替代 `uvx nox -s pytest`
  - 代码检查：`python -m ruff/black/isort` 替代 `uvx nox -s lint`
  - 文档构建：`python -m sphinx` 替代 `uvx nox -s docs`
  - 发布：`python -m build` 和 `python -m twine` 替代 `uvx nox -s release`

### 5. Git 子模块初始化修复

- **添加递归子模块检出**：在所有 checkout 步骤中添加 `with: submodules: recursive` 配置
- **URL 替换配置**：添加 git 配置以替换 SSH URL 为 HTTPS URL
- **移除依赖**：移除对 `uvx nox -s init-submodules` 命令的依赖

### 6. 依赖安装优化

- **简化依赖安装**：统一使用 `python -m pip install` 安装依赖
- **移除特殊环境处理**：移除对 `.cargo/env` 的依赖和特殊环境处理
- **直接安装开发依赖**：直接安装所需的开发依赖和工具

## 优化后的工作流结构

```
.github/workflows/
├── main.yml              # 主工作流（PR 和 push 触发）
├── workflow-dispatch.yml # 手动触发工作流
├── release.yml           # 发布工作流（标签触发）
├── reusable-jobs.yml     # 可重用任务定义
├── bumpversion.yml       # 版本更新工作流
└── issue-translator.yml  # 问题翻译工作流
```

## 工作流执行逻辑

### 1. PR 和推送事件

- **构建任务**：在所有平台和 Python 版本上执行
- **测试任务**：仅在 PR 时在所有平台和 Python 版本上执行
- **代码检查任务**：仅在 PR 时在单一环境中执行一次
- **文档构建任务**：仅在 PR 时在单一环境中执行一次

### 2. 发布事件

- **构建任务**：在所有平台和 Python 版本上执行
- **文档构建任务**：在单一环境中执行一次
- **发布任务**：收集所有构建产物，发布到 PyPI

## 未来改进建议

1. **缓存优化**：添加依赖缓存，减少安装时间
2. **并行执行**：进一步优化任务并行度，减少总体执行时间
3. **条件执行**：基于文件变更选择性执行任务
4. **测试覆盖率**：添加测试覆盖率报告和阈值检查
5. **自动版本管理**：完善版本自动更新机制
