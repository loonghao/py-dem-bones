# Import built-in modules
import glob
import os
import platform
import sys
import time

# Import third-party modules
import nox

from nox_actions.utils import MODULE_NAME, THIS_ROOT, build_cpp_extension, retry_command


def pytest(session: nox.Session, skip_install: bool = False) -> None:
    """Run pytest tests with coverage.

    Args:
        session: The nox session.
        skip_install: If True, skip installing the package in development mode.
                     This is useful when the package is already installed or built.
    """
    # Install pytest and coverage dependencies with pip cache
    start_time = time.time()
    retry_command(
        session, session.install, "pytest>=7.3.1", "pytest-cov>=4.1.0", max_retries=3
    )
    session.log(f"Test dependencies installed in {time.time() - start_time:.2f}s")

    # Install package in development mode (unless skipped)
    if not skip_install:
        start_time = time.time()
        retry_command(session, session.install, "-e", ".", max_retries=3)
        session.log(f"Package installed in {time.time() - start_time:.2f}s")
    else:
        session.log("Skipping package installation as requested")

    # Determine test root directory
    test_root = os.path.join(THIS_ROOT, "tests")
    if not os.path.exists(test_root):
        test_root = os.path.join(THIS_ROOT, "src", MODULE_NAME, "test")

    # Run pytest with coverage
    session.run(
        "pytest",
        f"--cov={MODULE_NAME}",
        "--cov-report=xml:coverage.xml",
        f"--rootdir={test_root}",
    )


@nox.session
def pytest_skip_install(session: nox.Session) -> None:
    """Run pytest tests with coverage, skipping package installation.

    This is a convenience session for CI environments where the package
    is already built or installed.
    """
    # Install additional test dependencies that would normally come from the package
    retry_command(session, session.install, "numpy", max_retries=3)

    # In CI, we need to install the wheel that was built in the previous step
    if os.environ.get("CI") == "true":
        # On Windows, ensure Visual C++ Redistributable is available
        if platform.system() == "Windows":
            session.log("Checking for Visual C++ Redistributable")
            # We can't directly install the redistributable, but we can check if it's available
            # and provide instructions if it's not
            session.log(
                "Note: Visual C++ Redistributable must be installed on the CI runner"
            )
            session.log(
                "If DLL load errors occur, ensure the appropriate Visual C++ Redistributable is installed"
            )

            # Add the directory containing the DLL to the PATH environment variable
            # This helps Windows find dependent DLLs that might be in the same directory
            wheel_dir = os.path.join(THIS_ROOT, "wheelhouse")
            if os.path.exists(wheel_dir):
                os.environ["PATH"] = f"{wheel_dir};{os.environ.get('PATH', '')}"
                session.log(f"Added {wheel_dir} to PATH to help locate DLLs")

                # Also add the site-packages directory to PATH
                # This is where the installed package and its DLLs will be located
                import site

                site_packages = site.getsitepackages()
                for site_pkg in site_packages:
                    if os.path.exists(site_pkg):
                        os.environ["PATH"] = f"{site_pkg};{os.environ.get('PATH', '')}"
                        session.log(f"Added {site_pkg} to PATH to help locate DLLs")

                # Add Python directory to PATH
                python_dir = os.path.dirname(sys.executable)
                os.environ["PATH"] = f"{python_dir};{os.environ.get('PATH', '')}"
                session.log(f"Added Python directory {python_dir} to PATH")

                # Add DLLs directory to PATH
                dlls_dir = os.path.join(python_dir, "DLLs")
                if os.path.exists(dlls_dir):
                    os.environ["PATH"] = f"{dlls_dir};{os.environ.get('PATH', '')}"
                    session.log(f"Added Python DLLs directory {dlls_dir} to PATH")

                # Add Windows System32 directory to PATH (in case it's not already there)
                system32_dir = os.path.join(
                    os.environ.get("SystemRoot", "C:\\Windows"), "System32"
                )
                if os.path.exists(system32_dir) and system32_dir not in os.environ.get(
                    "PATH", ""
                ):
                    os.environ["PATH"] = f"{system32_dir};{os.environ.get('PATH', '')}"
                    session.log(f"Added System32 directory {system32_dir} to PATH")

        # Get Python version info
        py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        # Determine platform tag based on the current system
        if platform.system() == "Windows":
            platform_tag = "win_amd64"
        elif platform.system() == "Linux":
            platform_tag = "linux_x86_64"
        else:
            platform_tag = "macosx_10_9_x86_64"

        # Find wheels matching the current Python version
        wheel_pattern = f"*cp{py_version.replace('.', '')}-*{platform_tag}*.whl"
        wheel_files = glob.glob(os.path.join(THIS_ROOT, "wheelhouse", wheel_pattern))

        # If no exact match, try a more general pattern
        if not wheel_files:
            wheel_pattern = f"*cp{py_version.replace('.', '')}*.whl"
            wheel_files = glob.glob(
                os.path.join(THIS_ROOT, "wheelhouse", wheel_pattern)
            )

        # If still no match, try any wheel as fallback
        if not wheel_files:
            wheel_files = glob.glob(os.path.join(THIS_ROOT, "wheelhouse", "*.whl"))

        if wheel_files:
            wheel_file = wheel_files[0]
            session.log(f"Installing wheel: {wheel_file}")
            # Install delvewheel to fix DLL dependencies
            session.log("Installing delvewheel to fix DLL dependencies...")
            session.install("delvewheel")

            # Try to fix the wheel with delvewheel
            if wheel_file and os.path.exists(wheel_file) and sys.platform == "win32":
                fixed_wheel_dir = os.path.join(
                    os.path.dirname(wheel_file), "fixed_wheels"
                )
                os.makedirs(fixed_wheel_dir, exist_ok=True)

                session.log(f"Fixing wheel {wheel_file} with delvewheel...")
                try:
                    session.run(
                        "delvewheel",
                        "repair",
                        "--wheel-dir",
                        fixed_wheel_dir,
                        wheel_file,
                        silent=True,
                    )

                    # Find the fixed wheel
                    fixed_wheels = glob.glob(os.path.join(fixed_wheel_dir, "*.whl"))
                    if fixed_wheels:
                        wheel_file = fixed_wheels[0]
                        session.log(f"Installing fixed wheel: {wheel_file}")
                        session.install(wheel_file)

                        # Extract and copy DLL files from the wheel to the Python directory
                        session.log("Extracting DLL files from the wheel...")
                        wheel_extract_dir = os.path.join(
                            os.path.dirname(wheel_file), "wheel_extract"
                        )
                        os.makedirs(wheel_extract_dir, exist_ok=True)

                        # Unpack the wheel
                        try:
                            session.run(
                                "python",
                                "-m",
                                "wheel",
                                "unpack",
                                "-d",
                                wheel_extract_dir,
                                wheel_file,
                                silent=True,
                            )
                        except Exception as e:
                            session.log(f"Error unpacking wheel: {e}")

                        # Find all DLL files in the extracted wheel
                        dll_files = []
                        for root, _, files in os.walk(wheel_extract_dir):
                            for file in files:
                                if file.lower().endswith(
                                    ".dll"
                                ) or file.lower().endswith(".pyd"):
                                    dll_files.append(os.path.join(root, file))

                        if dll_files:
                            session.log(
                                f"Found {len(dll_files)} DLL/PYD files in the wheel"
                            )

                            # Get Python directory
                            python_dir = os.path.dirname(sys.executable)
                            site_packages_dir = site.getsitepackages()[0]

                            # Copy DLL files to Python directory and site-packages
                            for dll_file in dll_files:
                                dll_name = os.path.basename(dll_file)
                                # Copy to Python directory
                                python_dll_path = os.path.join(python_dir, dll_name)
                                import shutil

                                shutil.copy2(dll_file, python_dll_path)
                                session.log(f"Copied {dll_name} to {python_dir}")

                                # Copy to site-packages directory
                                site_pkg_dll_path = os.path.join(
                                    site_packages_dir, dll_name
                                )
                                shutil.copy2(dll_file, site_pkg_dll_path)
                                session.log(f"Copied {dll_name} to {site_packages_dir}")
                    else:
                        session.log("No fixed wheels found. Using original wheel.")
                except Exception as e:
                    session.log(f"Error fixing wheel with delvewheel: {e}")
                    session.log("Continuing with original wheel...")
                    session.install(wheel_file)
            else:
                # Install the original wheel if not on Windows or if delvewheel repair failed
                if wheel_file and os.path.exists(wheel_file):
                    session.install(wheel_file)

                # After installing the wheel, try to extract any DLLs from it and add them to PATH
                if platform.system() == "Windows":
                    import zipfile

                    try:
                        with zipfile.ZipFile(wheel_file, "r") as wheel_zip:
                            # 查找所有DLL文件
                            dll_files = [
                                f for f in wheel_zip.namelist() if f.endswith(".dll")
                            ]
                            if dll_files:
                                # Extract DLLs to a temporary directory
                                import tempfile

                                dll_dir = tempfile.mkdtemp()
                                for dll_file in dll_files:
                                    wheel_zip.extract(dll_file, dll_dir)
                                    session.log(f"Extracted {dll_file} to {dll_dir}")

                                # 将提取的DLL目录添加到PATH
                                os.environ[
                                    "PATH"
                                ] = f"{dll_dir};{os.environ.get('PATH', '')}"
                                session.log(
                                    f"Added extracted DLLs directory {dll_dir} to PATH"
                                )

                                # 尝试复制DLL到Python的DLLs目录
                                python_dlls_dir = os.path.join(python_dir, "DLLs")
                                if os.path.exists(python_dlls_dir):
                                    import shutil

                                    for dll_file in dll_files:
                                        src_path = os.path.join(dll_dir, dll_file)
                                        dst_path = os.path.join(
                                            python_dlls_dir, os.path.basename(dll_file)
                                        )
                                        try:
                                            shutil.copy2(src_path, dst_path)
                                            session.log(
                                                f"Copied {dll_file} to Python DLLs directory"
                                            )
                                        except Exception as e:
                                            session.log(
                                                f"Failed to copy {dll_file} to Python DLLs directory: {e}"
                                            )
                    except Exception as e:
                        session.log(f"Error extracting DLLs from wheel: {e}")

                # 尝试在site-packages目录中查找_py_dem_bones.pyd文件
                try:
                    import site

                    site_packages = site.getsitepackages()
                    for site_pkg in site_packages:
                        pyd_path = os.path.join(
                            site_pkg, "py_dem_bones", "_py_dem_bones.pyd"
                        )
                        if os.path.exists(pyd_path):
                            session.log(f"Found _py_dem_bones.pyd at {pyd_path}")
                            # 使用Dependency Walker或类似工具检查依赖
                            try:
                                import subprocess

                                # 使用dumpbin检查DLL依赖（如果可用）
                                dumpbin_path = shutil.which("dumpbin")
                                if dumpbin_path:
                                    result = subprocess.run(
                                        [dumpbin_path, "/DEPENDENTS", pyd_path],
                                        capture_output=True,
                                        text=True,
                                    )
                                    session.log(
                                        f"DLL dependencies for _py_dem_bones.pyd:\n{result.stdout}"
                                    )
                            except Exception as e:
                                session.log(f"Failed to check DLL dependencies: {e}")
                except Exception as e:
                    session.log(f"Error locating _py_dem_bones.pyd: {e}")

                # 打印当前环境变量和已加载的DLL信息，帮助调试
                session.log("Current PATH environment variable:")
                session.log(os.environ.get("PATH", ""))

                # 尝试列出已安装的包及其位置
                try:
                    session.log("Installed packages:")
                    session.run("python", "-m", "pip", "list", "-v", silent=True)
                except Exception as e:
                    session.log(f"Error listing packages: {e}")

                # 尝试安装并使用delvewheel修复wheel包
                try:
                    session.log("Installing delvewheel to fix DLL dependencies...")
                    retry_command(session, session.install, "delvewheel", max_retries=3)

                    # 使用delvewheel修复wheel包
                    if wheel_files:
                        wheel_file = wheel_files[0]
                        fixed_wheel_dir = os.path.join(THIS_ROOT, "fixed_wheels")
                        os.makedirs(fixed_wheel_dir, exist_ok=True)

                        session.log(f"Fixing wheel {wheel_file} with delvewheel...")
                        try:
                            session.run(
                                "delvewheel",
                                "repair",
                                "--wheel-dir",
                                fixed_wheel_dir,
                                wheel_file,
                                silent=True,
                            )

                            # 查找修复后的wheel包
                            fixed_wheel_files = glob.glob(
                                os.path.join(fixed_wheel_dir, "*.whl")
                            )
                            if fixed_wheel_files:
                                fixed_wheel = fixed_wheel_files[0]
                                session.log(f"Installing fixed wheel: {fixed_wheel}")
                                retry_command(
                                    session, session.install, fixed_wheel, max_retries=3
                                )
                        except Exception as e:
                            session.log(f"Failed to fix wheel with delvewheel: {e}")
                except Exception as e:
                    session.log(f"Error using delvewheel: {e}")
        else:
            session.log("No matching wheel files found in wheelhouse directory")

    # 在运行测试前，先尝试导入模块，以便获取更详细的错误信息
    if platform.system() == "Windows":
        try:
            session.log("Testing module import before running tests...")
            session.run(
                "python",
                "-c",
                (
                    f"import {MODULE_NAME}; "
                    f"print(f'Successfully imported {MODULE_NAME} "
                    f'{{getattr({MODULE_NAME}, "__version__", "unknown")}}\')'
                ),
                silent=True,
            )
            session.log(f"Successfully imported {MODULE_NAME}")
        except Exception as e:
            session.log(f"Warning: Failed to import {MODULE_NAME}: {e}")
            session.log("Continuing with tests anyway...")

    # Run the main pytest function with skip_install=True
    pytest(session, skip_install=True)


def basic_test(session: nox.Session) -> None:
    """Run a basic test to verify that the package can be imported and used."""
    # Install package in development mode with pip cache
    start_time = time.time()
    retry_command(session, session.install, "-e", ".", max_retries=3)
    session.log(f"Package installed in {time.time() - start_time:.2f}s")

    # Run a basic import test
    session.run(
        "python", "-c", f"import {MODULE_NAME}; print({MODULE_NAME}.__version__)"
    )


def build_test(session: nox.Session) -> None:
    """Build the project and run tests."""
    # Build C++ extension
    build_success = build_cpp_extension(session)
    if not build_success:
        session.error("Failed to build C++ extension")

    # Run pytest
    pytest(session)


def find_latest_wheel(dist_dir: str = "dist") -> str:
    """Find the latest wheel file in the dist directory.

    Args:
        dist_dir: The directory to search for wheel files.

    Returns:
        The path to the latest wheel file, or None if no wheel files are found.
    """
    wheel_files = glob.glob(os.path.join(THIS_ROOT, dist_dir, "*.whl"))
    if not wheel_files:
        return None
    return max(wheel_files, key=os.path.getctime)


def build_no_test(session: nox.Session) -> None:
    """Build the package without running tests."""
    # Build the package
    session.log("Building package...")
    start_time = time.time()
    build_success = build_cpp_extension(session)
    session.log(f"Package built in {time.time() - start_time:.2f}s")
    if not build_success:
        session.error("Failed to build C++ extension.")
        return

    # Get the latest built wheel
    session.log("Getting latest built wheel...")
    latest_wheel = find_latest_wheel()
    if latest_wheel:
        session.log(f"Successfully built wheel: {os.path.basename(latest_wheel)}")
    else:
        session.log("Warning: No wheel found after build.")


def test_windows_compatibility(session: nox.Session) -> None:
    """Test Windows compatibility by building and testing on Windows.

    This session is specifically designed for testing Windows compatibility
    and ensuring proper DLL loading.
    """
    # Check if we're on Windows
    if platform.system() != "Windows":
        session.skip("This session is only for Windows platforms")

    # Install build dependencies including CMake
    retry_command(
        session,
        session.install,
        "build",
        "wheel",
        "setuptools>=42.0.0",
        "scikit-build-core>=0.5.0",
        "pybind11>=2.10.0",
        "numpy>=1.20.0",
        "cmake>=3.15",  # 确保安装 CMake
        max_retries=3,
    )

    # 验证 CMake 是否已安装
    session.run("cmake", "--version", silent=True)
    session.log("CMake installed successfully")

    # Build the wheel
    session.log("Building wheel for Windows...")
    session.run("python", "-m", "build", "--wheel", "--no-isolation")

    # Find the wheel file
    wheel_file = find_latest_wheel()
    if not wheel_file:
        session.error("Failed to build wheel")

    # Install the wheel
    session.log(f"Installing wheel: {wheel_file}")
    retry_command(session, session.install, wheel_file, max_retries=3)

    # Install test dependencies
    retry_command(
        session, session.install, "pytest>=7.3.1", "pytest-cov>=4.1.0", max_retries=3
    )

    # Test import
    session.log("Testing import...")
    import_statement = (
        f"import {MODULE_NAME}; "
        f"print(f'Successfully imported {MODULE_NAME} {{getattr({MODULE_NAME}, \""
        f'__version__", "unknown")}}\')'
    )
    session.run("python", "-c", import_statement)

    # Run basic tests
    test_root = os.path.join(THIS_ROOT, "tests")
    if not os.path.exists(test_root):
        test_root = os.path.join(THIS_ROOT, "src", MODULE_NAME, "test")

    session.log("Running tests...")
    session.run("pytest", f"--rootdir={test_root}", "tests/test_basic.py", "-v")
