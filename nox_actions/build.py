# Import built-in modules
import os
import platform
import shutil
import time

# Import third-party modules
import nox

from nox_actions.utils import MODULE_NAME, THIS_ROOT, build_cpp_extension, retry_command


def build(session: nox.Session) -> None:
    """Build the package using scikit-build-core."""
    # Install build dependencies with pip cache
    start_time = time.time()
    retry_command(session, session.install, "-e", ".[build]", max_retries=3)
    retry_command(session, session.install, "-e", ".", max_retries=3)
    session.log(f"Dependencies installed in {time.time() - start_time:.2f}s")

    # Clean previous build files
    clean_dirs = ["build", "dist", "_skbuild", f"{MODULE_NAME}.egg-info"]
    for dir_name in clean_dirs:
        dir_path = os.path.join(THIS_ROOT, dir_name)
        if os.path.exists(dir_path):
            session.log(f"Cleaning {dir_path}")
            shutil.rmtree(dir_path)

    # Create wheel directly using pip wheel
    os.makedirs("dist", exist_ok=True)

    # Set environment variables for build
    env = os.environ.copy()
    env["SKBUILD_BUILD_VERBOSE"] = "1"  # 使用新的环境变量
    env["FORCE_BDIST_WHEEL_PLAT"] = ""

    # Build C++ extension
    build_success = build_cpp_extension(session, env=env)

    if not build_success:
        session.log("Warning: C++ extension build failed")
        return

    # Build using PEP 517 build system
    session.log("Building package using PEP 517 build system...")
    try:
        session.run(
            "python",
            "-m",
            "build",
            "--wheel",
            "--outdir",
            "dist/",
            env=env,
            external=True,
        )
        session.log("PEP 517 build completed successfully")
    except Exception as e:
        session.log(f"PEP 517 build failed: {e}")
        session.log("Falling back to pip wheel...")
        try:
            session.run(
                "python",
                "-m",
                "pip",
                "wheel",
                ".",
                "-w",
                "dist/",
                "--no-deps",
                env=env,
                external=True,
            )
            session.log("Pip wheel build completed successfully")
        except Exception as e2:
            session.log(f"Pip wheel build also failed: {e2}")
            return

    # List the built wheels
    if os.path.exists(os.path.join(THIS_ROOT, "dist")):
        wheels = os.listdir(os.path.join(THIS_ROOT, "dist"))
        for wheel in wheels:
            if wheel.endswith(".whl"):
                session.log(f"Built wheel: {wheel}")


def build_wheels(session: nox.Session) -> None:
    """Build wheels for multiple platforms using cibuildwheel."""
    # Install cibuildwheel
    session.log("Installing cibuildwheel...")
    retry_command(session, session.install, "cibuildwheel", "wheel", max_retries=3)

    # Clean previous build files
    clean_dirs = ["build", "dist", "_skbuild", "wheelhouse", f"{MODULE_NAME}.egg-info"]
    for dir_name in clean_dirs:
        dir_path = os.path.join(THIS_ROOT, dir_name)
        if os.path.exists(dir_path):
            session.log(f"Cleaning {dir_path}")
            shutil.rmtree(dir_path)

    # Create output directories
    os.makedirs("wheelhouse", exist_ok=True)

    # Set environment variables for cibuildwheel
    env = os.environ.copy()
    env["CIBW_BUILD_VERBOSITY"] = "3"
    env["SKBUILD_BUILD_VERBOSE"] = "1"
    env["FORCE_BDIST_WHEEL_PLAT"] = ""

    # 检测操作系统
    is_windows = platform.system() == "Windows"

    if is_windows:
        session.log("检测到 Windows 环境，使用替代方法构建 wheel...")
        # 在 Windows 上，使用标准的 build 方法
        build(session)

        # 如果 build 成功，将生成的 wheel 文件复制到 wheelhouse 目录
        if os.path.exists(os.path.join(THIS_ROOT, "dist")):
            wheels = [
                f
                for f in os.listdir(os.path.join(THIS_ROOT, "dist"))
                if f.endswith(".whl")
            ]
            if wheels:
                for wheel in wheels:
                    src = os.path.join(THIS_ROOT, "dist", wheel)
                    dst = os.path.join(THIS_ROOT, "wheelhouse", wheel)
                    session.log(f"复制 wheel 文件: {wheel}")
                    shutil.copy2(src, dst)
            else:
                session.log("未找到 wheel 文件")
        return

    # 非 Windows 环境使用 cibuildwheel
    session.log("Building wheels with cibuildwheel...")
    platform_arg = "auto"  # Build for current platform

    try:
        session.run(
            "python",
            "-m",
            "cibuildwheel",
            "--platform",
            platform_arg,
            env=env,
            external=True,
        )
        session.log("cibuildwheel build completed successfully")
    except Exception as e:
        session.log(f"cibuildwheel build failed: {e}")
        session.log("Falling back to standard build...")
        build(session)
        return

    # List the built wheels
    if os.path.exists(os.path.join(THIS_ROOT, "wheelhouse")):
        wheels = os.listdir(os.path.join(THIS_ROOT, "wheelhouse"))
        for wheel in wheels:
            if wheel.endswith(".whl"):
                session.log(f"Built wheel: {wheel}")

    # Verify wheel tags
    session.log("Verifying wheel tags...")
    try:
        for wheel in os.listdir(os.path.join(THIS_ROOT, "wheelhouse")):
            if wheel.endswith(".whl"):
                session.run(
                    "python",
                    "-m",
                    "wheel",
                    "tags",
                    os.path.join(THIS_ROOT, "wheelhouse", wheel),
                    external=True,
                )
    except Exception as e:
        session.log(f"Wheel verification failed: {e}")


def install(session: nox.Session) -> None:
    """Install the package in development mode."""
    session.install("-e", ".[dev]")
    session.run(
        "python", "-c", f"import {MODULE_NAME}; print({MODULE_NAME}.__version__)"
    )


def clean(session: nox.Session) -> None:
    """Clean build artifacts."""
    dirs_to_clean = [
        "build",
        "dist",
        f"{MODULE_NAME}.egg-info",
        "_skbuild",
        ".pytest_cache",
        "wheelhouse",
    ]
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

    # Remove temporary build files
    temp_files = ["temp_build.bat"]
    for file_name in temp_files:
        file_path = os.path.join(THIS_ROOT, file_name)
        if os.path.exists(file_path):
            session.log(f"Removing {file_path}")
            os.remove(file_path)
