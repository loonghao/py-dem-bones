# CI/CD 流程

本文档描述了 py-dem-bones 项目的 CI/CD 流程，包括构建、测试和发布过程。

## GitHub Actions 工作流

项目使用 GitHub Actions 进行持续集成和部署。主要的工作流程包括：

### 1. Python Package 工作流

这个工作流在每次推送到主分支和拉取请求时运行，用于验证代码质量和功能。

主要步骤包括：
- 代码风格检查 (ruff, black, isort)
- 在多个平台和 Python 版本上运行单元测试
- 构建文档

### 2. Release 工作流

这个工作流在创建新的版本标签（如 `v0.2.1`）时运行，用于构建和发布包。

主要步骤包括：
- 使用 cibuildwheel 构建跨平台 wheel 文件
- 构建源代码分发包 (sdist)
- 构建文档
- 创建 GitHub Release
- 发布到 PyPI

## 使用 cibuildwheel

[cibuildwheel](https://cibuildwheel.readthedocs.io/) 是一个强大的工具，用于为多个平台和 Python 版本构建 wheel 包。我们的 CI 流程使用 cibuildwheel 来构建所有支持的平台和 Python 版本的 wheel 包。

### 配置文件

cibuildwheel 的配置位于以下两个文件中：

- `.cibuildwheel.toml`：主要配置文件，包含构建选项、环境设置等
- `pyproject.toml`：包含一些基本的 cibuildwheel 配置

### 本地构建

要在本地使用 cibuildwheel 构建 wheel 包，请按照以下步骤操作：

1. 安装 cibuildwheel：

```bash
pip install cibuildwheel
```

2. 运行 cibuildwheel：

```bash
# 构建当前平台的 wheel
python -m cibuildwheel --platform auto
```

或者使用 nox 命令：

```bash
python -m nox -s build-wheels
```

构建完成后，wheel 包将位于 `wheelhouse/` 目录中。

### 验证 wheel 包

构建完成后，可以使用以下命令验证 wheel 包的平台标签：

```bash
python -m nox -s verify-wheels
```

这将显示每个 wheel 包的平台标签，确保它们符合 PyPI 的要求。

## 发布新版本

要发布新版本，请按照以下步骤操作：

1. 更新 `CHANGELOG.md` 文件，添加新版本的变更记录
2. 更新 `pyproject.toml` 文件中的版本号
3. 提交更改并推送到 GitHub
4. 创建新的版本标签（如 `v0.2.2`）并推送到 GitHub：

```bash
git tag v0.2.2
git push origin v0.2.2
```

这将自动触发 Release 工作流，构建 wheel 文件并发布到 PyPI。

## 手动发布

如果需要手动发布，可以使用以下命令：

```bash
# 构建 wheel 和 sdist
python -m nox -s build-wheels

# 验证 wheel 包
python -m nox -s verify-wheels

# 发布到 PyPI
python -m nox -s publish
```

## 参考资料

- [cibuildwheel 文档](https://cibuildwheel.readthedocs.io/)
- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [PyPI 发布指南](https://packaging.python.org/en/latest/tutorials/packaging-projects/#uploading-the-distribution-archives)
- [NumPy CI 配置](https://github.com/numpy/numpy/tree/main/.github/workflows)
- [SciPy CI 配置](https://github.com/scipy/scipy/tree/main/.github/workflows)
