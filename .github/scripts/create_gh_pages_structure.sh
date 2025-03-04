#!/bin/bash
# 创建 GitHub Pages 目录结构和重定向文件
# 用法: ./create_gh_pages_structure.sh <docs_build_dir>

set -ex

# 获取当前目录的绝对路径
CURRENT_DIR=$(pwd)
DOCS_BUILD_DIR=${1:-"docs/_build/html"}
ROOT_DIR="${CURRENT_DIR}/gh-pages-root"
LATEST_DIR="${ROOT_DIR}/latest"

echo "Creating GitHub Pages directory structure..."
echo "Current directory: ${CURRENT_DIR}"
echo "Docs build directory: ${DOCS_BUILD_DIR}"
echo "Root directory: ${ROOT_DIR}"
echo "Latest directory: ${LATEST_DIR}"

# 1. 验证文档构建目录
if [ ! -d "${DOCS_BUILD_DIR}" ]; then
    echo "Warning: Docs build directory does not exist: ${DOCS_BUILD_DIR}"
    echo "Available directories in docs:"
    ls -la docs/
    echo "Creating empty docs build directory."
    mkdir -p "${DOCS_BUILD_DIR}"
    echo "<html><body><h1>Placeholder Documentation</h1></body></html>" > "${DOCS_BUILD_DIR}/index.html"
else
    echo "Docs build directory exists."
    ls -la "${DOCS_BUILD_DIR}"
fi

# 2. 创建目录结构
mkdir -p "${ROOT_DIR}"
mkdir -p "${LATEST_DIR}"

echo "Directory structure created:"
ls -la "${ROOT_DIR}"

# 3. 创建根目录的 index.html (重定向到latest)
cat > "${ROOT_DIR}/index.html" << EOF
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>py-dem-bones Documentation</title>
    <meta http-equiv="refresh" content="0; url=./latest/">
    <link rel="canonical" href="./latest/">
</head>
<body>
    <p>Redirecting to <a href="./latest/">latest documentation</a>...</p>
    <script>window.location.href = "./latest/";</script>
</body>
</html>
EOF

# 4. 复制文档文件到latest目录
echo "Copying documentation to latest directory..."
if [ -d "${DOCS_BUILD_DIR}" ] && [ "$(ls -A ${DOCS_BUILD_DIR})" ]; then
    mkdir -p "${LATEST_DIR}"
    cp -rv "${DOCS_BUILD_DIR}"/* "${LATEST_DIR}/"
    echo "Documentation files copied successfully."
else
    echo "Warning: No documentation files to copy."
    mkdir -p "${LATEST_DIR}"
    echo "<html><body><h1>No Documentation Available</h1></body></html>" > "${LATEST_DIR}/index.html"
fi

# 5. 验证复制操作
if [ ! -f "${LATEST_DIR}/index.html" ]; then
    echo "Warning: index.html not found in latest directory. Creating a placeholder."
    echo "<html><body><h1>Placeholder Documentation</h1></body></html>" > "${LATEST_DIR}/index.html"
else
    echo "Successfully verified documentation copy."
fi

ls -la "${LATEST_DIR}"
echo "GitHub Pages structure created and documentation copied successfully."
