# Wheel 构建指南

本目录包含用于构建和发布 py-dem-bones wheel 包的工具和配置。

## 使用 cibuildwheel 构建

[cibuildwheel](https://cibuildwheel.readthedocs.io/) 用于 Linux 和 macOS 的 CI wheel 构建。Windows CI 使用下文介绍的固定源码版本 msvc-kit action。

### 本地构建

要在本地使用 cibuildwheel 构建 wheel 包，有以下几种方法：

#### 在 Linux 或 macOS 上使用 nox

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
python -m cibuildwheel --config-file .cibuildwheel.toml --platform auto
```

请在项目根目录运行命令。`--config-file` 显式选择 `.cibuildwheel.toml`；cibuildwheel 的默认配置路径是 `pyproject.toml`。nox 和独立 wheel 脚本都会显式传递这一参数。生成的 wheel 位于 `wheelhouse/`。

### Windows 环境特殊说明

使用本机已有编译器进行 Windows 本地构建时，可以运行：

```bash
python tools/wheels/build_windows_wheel.py
```

该脚本安装构建依赖，先尝试显式传入配置文件的 cibuildwheel，再回退到 PEP 517 构建命令，并将 wheel 收集到 `wheelhouse/`。这些本地构建入口使用开发者环境，不下载便携工具链，也不生成下载凭据。

如果要主动选择已有的 msvc-kit 工具链，请使用专用构建入口，传入完整版本，并确保目标架构与当前 Python 一致：

请先安装 [Windows 工具链指南](../../docs/windows-toolchain.md) 列出的 Python 构建工具。

```powershell
python tools/wheels/build_msvc_wheel.py --msvc-kit C:/toolchains/msvc-kit.exe --dir C:/toolchains/native --msvc-version 14.44.35207 --sdk-version 10.0.26100.0 --host-arch x64 --arch x64 --output-dir wheelhouse
```

该入口执行 `doctor --compile`、校验 query 输出，以 Ninja 调用选定的编译器，修复运行时 DLL 依赖，并在干净虚拟环境中运行测试。它不会下载工具，也不会回退到其他编译器。已有下载凭据时可追加 `--lockfile`。修复后的 wheel 旁会生成 `toolchain-summary.json` 和 `wheel-summary.json`。ARM64 构建需使用 ARM64 Python，并将两个架构参数都设为 `arm64`。

### 配置文件

- `.cibuildwheel.toml`：`[tool.cibuildwheel]` 下的构建、修复和测试配置。
- `pyproject.toml`：包元数据和 scikit-build-core 配置。
- `tools/wheels/msvc-kit.json`：Windows CI 使用的固定 CLI 提交和完整 MSVC/SDK 版本。

运行 `python tools/wheels/check_configuration.py`，可以使用 CI 的 cibuildwheel 版本验证实际生效的配置，并在不编译 wheel 的情况下测试本地命令参数传递。

### CI 构建

共享构建 action 将 Linux 和 macOS 任务交给显式指定配置文件的 cibuildwheel。Windows 任务使用 `.github/actions/build-windows-wheel/action.yml`，从 `msvc-kit.json` 中的提交构建 CLI，根据微软清单校验下载档案，生成精确的锁定凭据，再通过 `build_msvc_wheel.py` 构建并测试一个原生 Python ABI。

发布工作流先构建全部必需产物。GitHub Releases 和 PyPI 发布仅在版本 tag 上执行；PR 和分支构建负责验证产物，不执行发布。

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
3. 尝试增加构建的详细程度：`CIBW_BUILD_VERBOSITY=3 python -m cibuildwheel --config-file .cibuildwheel.toml`。
4. 选定 Windows 工具链的构建失败时，先检查 doctor 报告和请求的版本。

## 参考资料

- [cibuildwheel 文档](https://cibuildwheel.readthedocs.io/)
- [scikit-build-core 文档](https://scikit-build-core.readthedocs.io/)
- [wheel 包格式规范](https://packaging.python.org/specifications/binary-distribution-format/)
- [PyPI 发布指南](https://packaging.python.org/tutorials/packaging-projects/#uploading-the-distribution-archives/)
