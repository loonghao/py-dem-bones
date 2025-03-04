# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## v0.2.2 (Unreleased)

### Added
- 集成 cibuildwheel 用于构建跨平台 wheel 文件
- 添加 `.cibuildwheel.toml` 配置文件
- 更新 CI/CD 工作流以使用 cibuildwheel
- 添加 macOS ARM64 (Apple Silicon) 支持
- 添加 wheel 验证工具和脚本
- 添加 nox 会话用于构建和验证 wheel 文件

### Changed
- 优化 CI/CD 工作流程，提高构建效率
- 更新 `pyproject.toml` 以支持 cibuildwheel
- 改进平台标签处理，确保兼容 PyPI 要求
- 更新文档，添加关于 wheel 构建的说明

## v0.2.1 (2025-03-03)

### Refactor

- add more examples

## v0.2.0 (2025-03-03)

### Feat

- Update version and expand documentation

## v0.1.0 (2025-03-03)

### Added
- Update project setup and add utilities
- Initial project structure
- Core bindings for DemBones and DemBonesExt
- Python wrapper classes for easier integration
- Basic NumPy integration
- Documentation framework
- Testing framework
- Cross-platform support (Windows, Linux, macOS)
- CI/CD pipeline with GitHub Actions

## v0.0.1 (2025-02-22)

### Added
- Initial repository setup
