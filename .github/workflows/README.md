# GitHub Actions 工作流

本项目使用优化的 GitHub Actions 工作流，确保高效的构建、测试和发布流程。

## 目录结构

```
.github/
├── scripts/              # 平台特定脚本
│   ├── linux/            # Linux 平台脚本
│   │   └── setup_eigen.sh
│   ├── mac/              # macOS 平台脚本
│   │   └── setup_eigen.sh
│   ├── win/              # Windows 平台脚本
│   │   └── setup_eigen.sh
│   └── py37/             # Python 3.7 特定脚本
│       └── setup_env.sh
└── workflows/            # GitHub Actions 工作流
    ├── build_wheels.yml  # 使用 cibuildwheel 构建轮子
    ├── release.yml       # 发布工作流（标签触发）
    ├── bumpversion.yml   # 版本更新工作流
    ├── docs.yml          # 文档构建工作流
    ├── lint.yml          # 代码检查工作流
    └── issue-translator.yml # 问题翻译工作流
```

## 工作流说明

### 构建轮子工作流 (`build_wheels.yml`)

使用 cibuildwheel 构建跨平台的 Python 轮子。它执行以下任务：

- **构建任务**: 在所有支持的平台（Ubuntu、macOS、Windows）和 Python 版本（3.7-3.12）上构建包
- **ARM64 支持**: 支持 Linux 和 macOS 的 ARM64 架构
- **测试任务**: 在所有支持的平台和 Python 版本上运行测试

### 发布工作流 (`release.yml`)

当创建新的版本标签（以 'v' 开头）时自动运行，执行以下任务：

- 使用 cibuildwheel 在所有支持的平台和 Python 版本上构建包
- 构建文档
- 创建 GitHub Release
- 发布包到 PyPI

### 代码检查工作流 (`lint.yml`)

在 PR 时运行代码检查，确保代码质量。

### 文档构建工作流 (`docs.yml`)

在 PR 时构建文档，确保文档正确。

## 优化特点

1. **资源优化**: 代码检查和文档构建任务只在单一环境中执行一次，避免重复执行
2. **Python 版本支持**: 支持 Python 3.7 到 3.12 版本
3. **平台覆盖**: 在 Ubuntu、macOS 和 Windows 上进行测试
4. **模块化设计**: 使用可重用任务，简化工作流维护
5. **自动发布**: 标签推送时自动构建并发布到 PyPI

## 使用方法

- **自动构建和测试**: 创建 Pull Request 或推送到主分支
- **手动触发特定任务**: 在 GitHub Actions 页面选择 "Workflow Dispatch" 工作流
- **发布新版本**: 创建以 'v' 开头的新标签（如 v0.1.0）

## GitHub Actions Workflows

This directory contains GitHub Actions workflows for the `py-dem-bones` project. These workflows automate various tasks such as testing, building, documentation generation, and releases.

## Workflows

### 1. Build Wheels Workflow (`build_wheels.yml`)

This workflow uses cibuildwheel to build cross-platform Python wheels. It performs the following tasks:

- **Building**: Builds wheels for all supported platforms (Ubuntu, macOS, Windows) and Python versions (3.7-3.12)
- **ARM64 Support**: Supports ARM64 architecture for Linux and macOS
- **Testing**: Runs tests on all supported platforms and Python versions

### 2. Release Workflow (`release.yml`)

This workflow creates a release when a new version tag is pushed to the repository. It performs the following tasks:

- Uses cibuildwheel to build wheels for all supported platforms and Python versions
- Creates a GitHub release with release notes
- Publishes the package to PyPI

### 3. Lint Workflow (`lint.yml`)

This workflow runs code quality checks on pull requests to ensure code quality.

### 4. Documentation Workflow (`docs.yml`)

This workflow builds documentation on pull requests to ensure documentation correctness.

### 5. Bump Version Workflow (`bumpversion.yml`)

This workflow automatically bumps the version and creates a changelog based on commit messages. It runs when code is pushed to the `main` branch.

Key features:
- Uses [Commitizen](https://github.com/commitizen-tools/commitizen) to determine the next version
- Creates a changelog based on commit messages
- Commits the version bump and changelog to the repository

## Usage

### Commit Messages

To ensure proper versioning, follow the [Conventional Commits](https://www.conventionalcommits.org/) format for your commit messages:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Where `type` is one of:
- `feat`: A new feature (triggers a minor version bump)
- `fix`: A bug fix (triggers a patch version bump)
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Breaking changes should be indicated with a `!` after the type/scope or with `BREAKING CHANGE:` in the footer, which will trigger a major version bump.

### Manual Workflow Dispatch

The main workflow can be manually triggered using the "workflow_dispatch" event in GitHub's UI. This is useful for running the workflow without making changes to the code.

### Permissions

The workflows require specific permissions to function correctly:
- `contents: write`: For pushing to branches and creating releases
- `pull-requests: write`: For adding comments to PRs
- `pages: write`: For deploying to GitHub Pages

## Troubleshooting

### 404 Errors on GitHub Pages

If you encounter 404 errors when accessing the documentation:

1. Ensure GitHub Pages is enabled in the repository settings
2. Check that the source is set to the `gh-pages` branch
3. Wait a few minutes for GitHub Pages to deploy after the workflow completes
4. Verify that the `gh-pages` branch contains the expected content

### Failed Workflow Runs

If a workflow run fails:

1. Check the workflow logs for error messages
2. Ensure all dependencies are correctly specified
3. Verify that the required secrets are configured in the repository settings
4. Try running the failing steps locally to debug the issue

## Environment Variables

- `SKIP_CMAKE_BUILD`: Set to `1` to skip the CMake build step when building documentation
- `PERSONAL_ACCESS_TOKEN`: GitHub token with required permissions for version bumping and releases
