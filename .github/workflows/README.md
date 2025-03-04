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
    ├── main.yml          # 主工作流（PR 和 push 触发）
    ├── workflow-dispatch.yml # 手动触发工作流
    ├── release.yml       # 发布工作流（标签触发）
    ├── reusable-jobs.yml # 可重用任务定义
    ├── bumpversion.yml   # 版本更新工作流
    └── issue-translator.yml # 问题翻译工作流
```

## 工作流说明

### 主工作流 (`main.yml`)

主工作流在代码推送到主分支或创建 Pull Request 时自动运行。它执行以下任务：

- **构建任务**: 在所有支持的平台（Ubuntu、macOS、Windows）和 Python 版本（3.7-3.13）上构建包
- **测试任务**: 在 PR 时在所有支持的平台和 Python 版本上运行测试
- **代码检查任务**: 在 PR 时只在 Python 3.11 + Ubuntu 环境中执行一次
- **文档构建任务**: 在 PR 时只在 Python 3.10 + Ubuntu 环境中执行一次

### 手动触发工作流 (`workflow-dispatch.yml`)

允许手动触发特定任务，支持以下选项：

- **all**: 运行所有任务
- **build**: 只运行构建任务
- **test**: 只运行测试任务
- **lint**: 只运行代码检查任务
- **docs**: 只运行文档构建任务
- **release**: 只运行发布任务（不会实际发布到 PyPI）

### 发布工作流 (`release.yml`)

当创建新的版本标签（以 'v' 开头）时自动运行，执行以下任务：

- 在所有支持的平台和 Python 版本上构建包
- 构建文档
- 创建 GitHub Release
- 发布包到 PyPI

### 可重用任务 (`reusable-jobs.yml`)

定义了可在其他工作流中重用的任务：

- **build-and-test**: 构建和测试任务
- **lint**: 代码检查任务
- **docs**: 文档构建任务
- **release**: 发布任务

## 优化特点

1. **资源优化**: 代码检查和文档构建任务只在单一环境中执行一次，避免重复执行
2. **Python 版本支持**: 支持 Python 3.7 到 3.13 版本
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

### 1. Main Workflow (`main.yml`)

The main workflow runs on pull requests to the `main` branch and when code is pushed to the `main` branch. It performs the following tasks:

- **Linting**: Checks code quality using tools like Ruff, Black, and isort
- **Building**: Builds the project to ensure it compiles correctly
- **Testing**: Runs unit tests across different Python versions and operating systems
- **Documentation**:
  - For PRs: Builds and deploys a preview of the documentation
  - For main branch: Builds and deploys the latest documentation

#### Documentation URLs

- **Latest Documentation**: https://[owner].github.io/py-dem-bones/latest/
- **PR Previews**: https://[owner].github.io/py-dem-bones/pr-preview/[PR_NUMBER]/

### 2. Bump Version Workflow (`bumpversion.yml`)

This workflow automatically bumps the version and creates a changelog based on commit messages. It runs when code is pushed to the `main` branch.

Key features:
- Uses [Commitizen](https://github.com/commitizen-tools/commitizen) to determine the next version
- Creates a changelog based on commit messages
- Commits the version bump and changelog to the repository

### 3. Release Workflow (`release.yml`)

This workflow creates a release when a new version tag is pushed to the repository. It performs the following tasks:

- Builds the project for different platforms
- Creates a GitHub release with release notes
- Publishes the package to PyPI

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
