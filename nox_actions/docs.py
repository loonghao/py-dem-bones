"""Documentation related nox actions."""
import os
import shutil
from pathlib import Path

import nox

from nox_actions.utils import get_package_name


def generate_stubs(session: nox.Session) -> bool:
    """Generate type stubs for pybind11 modules using pybind11-stubgen.
    
    Args:
        session: The nox session.
        
    Returns:
        bool: True if stubs were generated successfully, False otherwise.
    """
    package_name = get_package_name()
    
    # 安装 pybind11-stubgen
    session.install("pybind11-stubgen")
    
    # 检查是否设置了跳过构建的环境变量
    skip_build = os.environ.get("SKIP_CMAKE_BUILD", "0") == "1"
    
    # 如果没有跳过构建，则安装包
    if not skip_build:
        # 确保包已安装，以便 pybind11-stubgen 可以导入它
        session.install("-e", ".")
    
    # 创建输出目录
    output_dir = Path("src") / f"{package_name}-stubs"
    os.makedirs(output_dir, exist_ok=True)
    
    # 运行 pybind11-stubgen 生成存根文件
    try:
        session.run(
            "pybind11-stubgen",
            package_name,
            "--output-dir", str(output_dir.parent),
            silent=True
        )
        
        # 检查是否成功生成了存根文件
        stub_files = list(output_dir.glob("**/*.pyi"))
        if not stub_files:
            session.log(f"No stub files were generated in {output_dir}")
            return False
            
        session.log(f"Generated {len(stub_files)} stub files in {output_dir}")
        
        # 将生成的存根文件复制到文档源目录
        docs_stubs_dir = Path("docs") / "_stubs"
        os.makedirs(docs_stubs_dir, exist_ok=True)
        
        for stub_file in stub_files:
            # 计算相对路径，以保持目录结构
            rel_path = stub_file.relative_to(output_dir)
            target_path = docs_stubs_dir / rel_path
            os.makedirs(target_path.parent, exist_ok=True)
            shutil.copy2(stub_file, target_path)
            
        session.log(f"Copied stub files to {docs_stubs_dir}")
        return True
        
    except Exception as e:
        session.log(f"Failed to generate stubs: {e}")
        return False


def docs(session: nox.Session) -> None:
    """Build the docs.

    Args:
        session: The nox session.
    """
    # 检查是否设置了跳过构建的环境变量
    skip_build = os.environ.get("SKIP_CMAKE_BUILD", "0") == "1"
    
    # Install dependencies.
    session.install(
        "sphinx",
        "furo",
        "sphinx-autobuild",
    )
    
    # 如果没有跳过构建，则安装包
    if not skip_build:
        session.install("-e", ".")
    
    # 生成类型提示存根文件
    stubs_generated = generate_stubs(session)
    if not stubs_generated:
        session.log(
            "Failed to generate type stubs. Documentation may be incomplete."
        )

    # 确保构建目录存在
    build_dir = Path("docs") / "_build"
    os.makedirs(build_dir, exist_ok=True)

    # 构建文档
    with session.chdir("docs"):
        session.run("sphinx-build", "-b", "html", ".", "_build/html")


def docs_serve(session: nox.Session) -> None:
    """Build and serve the docs with live reloading on file changes.

    Args:
        session: The nox session.
    """
    # 检查是否设置了跳过构建的环境变量
    skip_build = os.environ.get("SKIP_CMAKE_BUILD", "0") == "1"
    
    # Install dependencies.
    session.install(
        "sphinx",
        "furo",
        "sphinx-autobuild",
    )
    
    # 如果没有跳过构建，则安装包
    if not skip_build:
        session.install("-e", ".")

    # 生成类型提示存根文件
    stubs_generated = generate_stubs(session)
    if not stubs_generated:
        session.log(
            "Failed to generate type stubs. Documentation may be incomplete."
        )

    # 使用 sphinx-autobuild 提供实时重载功能
    with session.chdir("docs"):
        session.run(
            "sphinx-autobuild",
            ".",
            "_build/html",
            "--watch", "..",
            "--open-browser",
        )
