# VFX Platform Support

## Python Version Support

从版本0.7.0开始，py-dem-bones项目遵循[VFX平台](https://vfxplatform.com/)标准，仅支持Python 3.9及以上版本。

### 支持的Python版本

- Python 3.9
- Python 3.10
- Python 3.11
- Python 3.12

### 不再支持的Python版本

- Python 3.7（已于2023年6月27日结束生命周期）
- Python 3.8

## 平台支持

py-dem-bones支持以下平台：

- Windows
- macOS（最低部署目标：macOS 12.0）
- Linux

## 构建系统

项目使用以下工具进行构建：

- scikit-build-core：用于构建C++扩展
- pybind11：用于Python/C++绑定
- cibuildwheel：用于构建多平台wheel包

## 依赖管理

项目使用Poetry进行依赖管理。可以使用以下命令安装依赖：

```bash
# 安装基本依赖
poetry install

# 安装开发依赖
poetry install --with dev

# 安装测试依赖
poetry install --with test

# 安装文档依赖
poetry install --with docs
```

## 在DCC环境中使用

py-dem-bones主要设计用于数字内容创建(DCC)环境，如Blender、Maya、Houdini等。这些环境通常遵循VFX平台标准，因此py-dem-bones的版本支持策略与这些应用程序保持一致。

## 版本兼容性表

| py-dem-bones版本 | Python版本支持 | VFX平台年份 |
|-----------------|--------------|------------|
| 0.7.0+          | 3.9+         | CY2022+    |
| 0.6.x           | 3.7+         | CY2020+    |
