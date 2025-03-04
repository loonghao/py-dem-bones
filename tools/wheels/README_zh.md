# Wheel 构建指南

本目录包含用于构建和发布 py-dem-bones wheel 包的工具和配置。

## 使用 cibuildwheel 构建

[cibuildwheel](https://cibuildwheel.readthedocs.io/) 是一个强大的工具，用于为多个平台和 Python 版本构建 wheel 包。我们的 CI 流程使用 cibuildwheel 来构建所有支持的平台和 Python 版本的 wheel 包。

### 本地构建

要在本地使用 cibuildwheel 构建 wheel 包，有以下几种方法：

#### 使用 nox（推荐）

```bash
# 安装 nox
pip install nox

# 构建 wheel
python -m nox -s build-wheels

# 验证 wheel 包
python -m nox -s verify-wheels
```

#### 直接使用 cibuildwheel

1. 安装 cibuildwheel：

```bash
pip install cibuildwheel
```

2. 运行 cibuildwheel：

```bash
# 构建当前平台的 wheel
python -m cibuildwheel --platform auto
```

cibuildwheel 将使用项目根目录下的 `.cibuildwheel.toml` 配置文件来构建 wheel 包。构建完成后，wheel 包将位于 `./wheelhouse/` 目录中。

### Windows 环境特殊说明

在 Windows 环境中，由于 cibuildwheel 可能会遇到一些问题，我们提供了一个专门的脚本来构建 wheel 包：

```bash
python tools/wheels/build_windows_wheel.py
```

这个脚本会自动安装所需的依赖，并使用标准的 `python -m build` 命令构建 wheel 包。构建完成后，wheel 包将位于 `wheelhouse/` 目录中。

如果你在 Windows 环境中使用 nox 命令构建 wheel，它会自动检测操作系统并使用适当的方法：

```bash
python -m nox -s build-wheels
```

### 配置文件

cibuildwheel 的配置位于以下两个文件中：

- `.cibuildwheel.toml`：主要配置文件，包含构建选项、环境设置等
- `pyproject.toml`：包含一些基本的 cibuildwheel 配置

### CI 构建

GitHub Actions 工作流程 `.github/workflows/release.yml` 使用 cibuildwheel 为所有支持的平台和 Python 版本构建 wheel 包。当创建一个新的 tag 或手动触发工作流程时，CI 将自动构建 wheel 包并上传到 GitHub Releases 和 PyPI。

## 验证 wheel 包

我们提供了一个脚本来验证构建的 wheel 包的平台标签：

```bash
# 使用 nox 验证 wheel
python -m nox -s verify-wheels

# 或直接使用脚本
python tools/wheels/verify_wheels.py
```

这个脚本将检查 wheel 包是否具有正确的平台标签，并且可以在目标平台上安装。

## 发布到 PyPI

构建并验证 wheel 包后，可以将它们发布到 PyPI：

```bash
# 使用 nox
python -m nox -s publish

# 或直接使用 twine
python -m twine upload wheelhouse/*.whl
```

确保你已经在环境变量中设置了 PyPI 的凭据 `TWINE_USERNAME` 和 `TWINE_PASSWORD`，或者使用 twine 的 `--username` 和 `--password` 选项。

## 故障排除

如果你在 wheel 构建过程中遇到问题，以下是一些常见的解决方案：

1. 确保你已安装所有必需的依赖，包括 CMake 和 C++ 编译器。
2. 检查 cibuildwheel 日志以获取详细的错误信息。
3. 尝试增加构建的详细程度：`CIBW_BUILD_VERBOSITY=3 python -m cibuildwheel`。
4. 对于 Windows 特定的问题，尝试使用专门的 Windows 构建脚本。

## 参考资料

- [cibuildwheel 文档](https://cibuildwheel.readthedocs.io/)
- [scikit-build-core 文档](https://scikit-build-core.readthedocs.io/)
- [wheel 包格式规范](https://packaging.python.org/specifications/binary-distribution-format/)
- [PyPI 发布指南](https://packaging.python.org/tutorials/packaging-projects/#uploading-the-distribution-archives/)
