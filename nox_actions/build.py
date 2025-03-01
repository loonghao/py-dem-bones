# Import built-in modules
import os
import shutil

# Import third-party modules
import nox

from nox_actions.utils import MODULE_NAME, THIS_ROOT, build_cpp_extension


def build(session: nox.Session) -> None:
    """Build the package using scikit-build-core."""
    # 安装构建依赖
    session.install(
        "-e", ".",
        "build>=1.0.0",
    )

    # 清理之前的构建文件
    clean_dirs = ["build", "dist", "_skbuild", f"{MODULE_NAME}.egg-info"]
    for dir_name in clean_dirs:
        dir_path = os.path.join(THIS_ROOT, dir_name)
        if os.path.exists(dir_path):
            session.log(f"Cleaning {dir_path}")
            shutil.rmtree(dir_path)

    # 使用 pip wheel 直接创建轮子
    os.makedirs("dist", exist_ok=True)

    # 构建 C++ 扩展
    build_success = build_cpp_extension(session)
    
    if not build_success:
        session.log("Warning: C++ extension build failed")
        return

    # List the built wheels
    if os.path.exists(os.path.join(THIS_ROOT, "dist")):
        wheels = os.listdir(os.path.join(THIS_ROOT, "dist"))
        for wheel in wheels:
            if wheel.endswith(".whl"):
                session.log(f"Built wheel: {wheel}")


def install(session: nox.Session) -> None:
    """Install the package in development mode."""
    session.install("-e", ".[dev]")
    session.run("python", "-c", f"import {MODULE_NAME}; print({MODULE_NAME}.__version__)")


def clean(session: nox.Session) -> None:
    """Clean build artifacts."""
    dirs_to_clean = ["build", "dist", f"{MODULE_NAME}.egg-info", "_skbuild", ".pytest_cache"]
    for dir_name in dirs_to_clean:
        dir_path = os.path.join(THIS_ROOT, dir_name)
        if os.path.exists(dir_path):
            session.log(f"Removing {dir_path}")
            shutil.rmtree(dir_path)

    # Also clean __pycache__ directories
    for root, dirs, _ in os.walk(THIS_ROOT):
        for dir_name in dirs:
            if dir_name == "__pycache__":
                cache_dir = os.path.join(root, dir_name)
                session.log(f"Removing {cache_dir}")
                shutil.rmtree(cache_dir)

    # 删除临时构建文件
    temp_files = ["temp_build.bat"]
    for file_name in temp_files:
        file_path = os.path.join(THIS_ROOT, file_name)
        if os.path.exists(file_path):
            session.log(f"Removing {file_path}")
            os.remove(file_path)
