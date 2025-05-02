# CI 优化指南

本文档提供了关于如何优化 py-dem-bones 项目的 CI 构建和测试流程的指南，特别是针对解决构建卡住的问题。

## 常见问题及解决方案

### 1. 构建卡住或超时

**问题**：CI 构建过程中，特别是在编译 C++ 扩展时，构建过程可能会卡住或超时。

**解决方案**：
- 设置合理的超时时间（`timeout-minutes` 参数）
- 限制并行构建数量（`--parallel 2` 参数）
- 使用 ccache 加速重复构建
- 使用 Ninja 代替 Make 加速构建过程

### 2. 依赖安装问题

**问题**：依赖安装过程可能会失败或卡住。

**解决方案**：
- 使用 uv/uvx 代替 pip 进行更快的依赖安装
- 设置更长的超时时间（`PIP_DEFAULT_TIMEOUT` 环境变量）
- 禁用 pip 的缓存，使用 GitHub Actions 的缓存机制（`PIP_NO_CACHE_DIR` 环境变量）

### 3. 内存不足

**问题**：C++ 编译过程可能会消耗大量内存，导致 CI 运行器内存不足。

**解决方案**：
- 限制并行构建数量
- 使用 ccache 减少需要重新编译的文件数量
- 优化编译选项，减少内存使用

## 优化策略

### 使用 ccache

ccache 是一个编译器缓存工具，可以显著加速重复构建。我们已经在 `.github/workflows/optimized_build.yml` 中配置了 ccache：

```yaml
# 设置 ccache
- name: Setup ccache
  uses: actions/cache@v3
  with:
    path: .ccache
    key: ${{ matrix.config.name }}-ccache-${{ steps.ccache_cache_timestamp.outputs.timestamp }}
    restore-keys: |
      ${{ matrix.config.name }}-ccache-
```

### 使用 uv/uvx

uv/uvx 是一个快速的 Python 包安装器，可以加速依赖安装过程。我们已经在 `.github/workflows/optimized_test.yml` 中配置了 uv：

```yaml
# 安装 uv
- name: Install uv
  run: |
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo "$HOME/.cargo/bin" >> $GITHUB_PATH
  shell: bash
  if: runner.os != 'Windows'
```

### 限制并行构建

为了避免内存不足问题，我们限制了并行构建的数量：

```yaml
# 限制并行构建数量
- name: Build
  run: |
    cmake --build build --config Release --parallel 2
  shell: bash
```

### 设置合理的超时时间

为了避免构建卡住，我们设置了合理的超时时间：

```yaml
# 设置超时时间
timeout-minutes: 60  # 设置合理的超时时间
```

## 新增的 CI 工作流

我们添加了两个优化的 CI 工作流：

1. **optimized_build.yml**：使用 ccache 优化的构建工作流
2. **optimized_test.yml**：使用 uv/uvx 优化的多 Python 版本测试工作流

这些工作流已经配置了上述优化策略，应该能够解决构建卡住的问题。

## 使用建议

1. 如果构建仍然卡住，可以尝试进一步减少并行构建数量或增加超时时间。
2. 监控 ccache 统计信息，确保缓存命中率高。
3. 考虑使用更大的 GitHub Actions 运行器（例如 `large` 或 `xlarge`）来获取更多资源。

## 参考资料

- [Speeding up C++ GitHub Actions using ccache](https://cristianadam.eu/20200113/speeding-up-c-plus-plus-github-actions-using-ccache/)
- [GitHub Actions 缓存依赖项以加快工作流程](https://docs.github.com/zh/actions/using-workflows/caching-dependencies-to-speed-up-workflows)
- [uv: Python 包安装器和解析器](https://github.com/astral-sh/uv)
