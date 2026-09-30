# 使用cibuildwheel进行本地构建

本文档介绍如何使用cibuildwheel在本地环境中构建py-dem-bones的wheel包。

## 什么是cibuildwheel？

cibuildwheel是一个Python工具，用于构建Python wheel包，特别是那些包含C++扩展的包。它通常在CI环境中使用，但也可以在本地环境中使用。

## 在本地使用cibuildwheel的优势

1. **一致的构建环境**：使用与CI相同的构建工具，确保本地构建与CI构建一致
2. **自动处理依赖**：自动安装构建所需的依赖
3. **多平台支持**：可以在本地构建多个平台的wheel包（如果您的系统支持）
4. **自动测试**：构建后自动运行测试

## 使用nox运行cibuildwheel

我们提供了一个nox会话，用于在本地运行cibuildwheel：

```bash
nox -s cibuildwheel
```

这个命令会：
1. 安装cibuildwheel和其他依赖
2. 清理之前的构建文件
3. 使用cibuildwheel构建当前Python版本的wheel包
4. 安装构建的wheel包
5. 运行基本测试

## 手动运行cibuildwheel

如果您想手动运行cibuildwheel，可以按照以下步骤操作：

1. 安装cibuildwheel：
   ```bash
   pip install cibuildwheel
   ```

2. 运行cibuildwheel：
   ```bash
   python -m cibuildwheel --platform auto --output-dir wheelhouse
   ```

3. 安装构建的wheel包：
   ```bash
   pip install wheelhouse/*.whl
   ```

4. 运行测试：
   ```bash
   pytest tests/test_basic.py
   ```

## 配置cibuildwheel

cibuildwheel的配置在`.cibuildwheel.toml`文件中。您可以根据需要修改这个文件，例如：

- 修改构建的Python版本
- 修改构建的平台
- 修改构建前后的命令
- 修改测试命令

详细的配置选项请参考[cibuildwheel文档](https://cibuildwheel.readthedocs.io/en/stable/options.html)。

## 常见问题

### 在Windows上使用cibuildwheel

在Windows上，我们使用setup.py直接构建wheel包，而不是使用cibuildwheel。这是因为在Windows上使用cibuildwheel和scikit-build-core可能会遇到元数据生成失败的问题。

使用setup.py构建需要以下依赖：
- Visual Studio构建工具（从[Visual Studio下载页面](https://visualstudio.microsoft.com/downloads/)下载）
- CMake
- Ninja
- Python开发包

当您运行`nox -s cibuildwheel`时，这些依赖会自动安装。

### 在Linux上使用cibuildwheel

在Linux上，cibuildwheel默认使用Docker来创建隔离的构建环境。确保您已安装Docker并且它正在运行。

如果您不想使用Docker，可以设置环境变量`CIBW_CONTAINER_ENGINE=none`：

```bash
CIBW_CONTAINER_ENGINE=none python -m cibuildwheel --platform linux
```

### 在macOS上使用cibuildwheel

在macOS上，cibuildwheel需要安装Xcode命令行工具。您可以通过运行以下命令安装：

```bash
xcode-select --install
```

## 更多信息

- [cibuildwheel文档](https://cibuildwheel.readthedocs.io/en/stable/)
- [py-dem-bones文档](https://loonghao.github.io/py-dem-bones)
