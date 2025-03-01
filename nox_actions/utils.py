# Import built-in modules
import os
import platform
import sys
from pathlib import Path

MODULE_NAME = "py_dem_bones"
THIS_ROOT = Path(__file__).parent.parent
PROJECT_ROOT = THIS_ROOT.parent


def _assemble_env_paths(*paths):
    """Assemble environment paths separated by a semicolon.

    Args:
        *paths: Paths to be assembled.

    Returns:
        str: Assembled paths separated by a semicolon.
    """
    return ";".join(paths)


def find_vcvarsall() -> str:
    """Find vcvarsall.bat on Windows.
    
    Returns:
        str: Path to vcvarsall.bat if found, empty string otherwise.
    """
    possible_paths = [
        r"C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvarsall.bat",
        r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvarsall.bat",
        r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Professional\VC\Auxiliary\Build\vcvarsall.bat",
        r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Enterprise\VC\Auxiliary\Build\vcvarsall.bat",
        # Visual Studio 2022 paths
        r"C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat",
        r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat",
        r"C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvarsall.bat",
        r"C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvarsall.bat",
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return ""


def setup_windows_environment(session, command_str: str, env=None) -> bool:
    """Set up Windows environment for building C++ code.
    
    Args:
        session: Nox session object.
        command_str: Command string to be executed in the Windows environment.
        env: Optional environment variables dictionary.
    
    Returns:
        bool: True if the environment was set up and command executed, False otherwise.
    """
    if platform.system() != "Windows":
        return False

    # In GitHub Actions environment, do not use vcvarsall.bat
    if os.environ.get("GITHUB_ACTIONS") == "true":
        session.log("Running in GitHub Actions, using default environment")
        try:
            # Directly execute the command
            if command_str.startswith("-m") or command_str.startswith("/"):
                session.run(sys.executable, *command_str.split(), env=env, external=True)
            else:
                session.run(command_str, env=env, external=True)
            return True
        except Exception as e:
            session.log(f"Error running command in GitHub Actions: {e}")
            return False

    # Local environment uses vcvarsall.bat
    vcvarsall = find_vcvarsall()
    if not vcvarsall:
        session.log("Could not find vcvarsall.bat. Please install Visual Studio Build Tools.")
        return False

    session.log(f"Using Visual Studio environment from: {vcvarsall}")
    # Create a batch file to set up the environment and run the command
    build_bat = os.path.join(THIS_ROOT, "temp_build.bat")
    with open(build_bat, "w") as f:
        f.write(f'call "{vcvarsall}" x64\n')

        # If there are environment variables, add them to the batch file
        if env:
            for key, value in env.items():
                f.write(f'set {key}={value}\n')

        # Get the full path of the Python interpreter
        python_path = sys.executable

        # If the command is not starting with python, add the Python interpreter path
        if command_str.startswith("-m") or command_str.startswith("/"):
            f.write(f'"{python_path}" {command_str}\n')
        else:
            f.write(f'{command_str}\n')

    # Run the batch file
    try:
        # Use external=True parameter
        session.run("cmd", "/c", build_bat, external=True)
        success = True
    except Exception as e:
        session.log(f"Error running command in Windows environment: {e}")
        success = False
    finally:
        # Clean up
        if os.path.exists(build_bat):
            os.remove(build_bat)

    return success


def build_cpp_extension(session, env=None):
    """Build C++ extension for the project.
    
    Args:
        session: Nox session object.
        env: Optional environment variables dictionary.
        
    Returns:
        bool: True if the build was successful, False otherwise.
    """
    session.log("Building C++ extension...")
    
    # Detect platform
    system = platform.system()
    session.log(f"Building on {system} platform")

    # Set environment variables to ensure consistent build configuration
    if env is None:
        env = os.environ.copy()
    env["SKBUILD_CMAKE_VERBOSE"] = "1"  # Enable verbose CMake output

    # Use pip wheel to directly create a wheel
    os.makedirs("dist", exist_ok=True)

    # 确保 pip 和必要的构建工具已安装
    try:
        session.run(sys.executable, "-m", "pip", "--version", silent=True)
    except Exception:
        session.log("pip not found, attempting to install...")
        try:
            # 尝试安装 pip
            session.run(sys.executable, "-m", "ensurepip", "--upgrade", silent=True)
            session.run(sys.executable, "-m", "pip", "install", "--upgrade", "pip", "wheel", "setuptools", "build")
        except Exception as e:
            session.log(f"Failed to install pip: {e}")
            return False

    # Execute different build commands based on the platform
    build_success = False
    wheel_cmd = "-m pip wheel . -w dist/ --no-deps"
    
    if system == "Windows":
        if setup_windows_environment(session, wheel_cmd, env):
            session.log("Windows extension build completed successfully")
            build_success = True
        else:
            session.log("Windows environment setup failed, falling back to direct build")
            try:
                session.run(
                    sys.executable, "-m", "pip", "wheel", ".",
                    "-w", "dist/", "--no-deps",
                    env=env, external=True
                )
                build_success = True
            except Exception as e:
                session.log(f"Error running command in Windows environment: {e}")
    else:  # Linux or macOS
        try:
            # Ensure using python -m pip instead of pip directly
            session.run(
                sys.executable, "-m", "pip", "wheel", ".",
                "-w", "dist/", "--no-deps",
                env=env, external=True
            )
            build_success = True
        except Exception as e:
            session.log(f"Failed to build extension: {e}")
            # Try installing wheel package and retry
            try:
                session.log("Attempting to install wheel package and retry...")
                session.run(sys.executable, "-m", "pip", "install", "--upgrade", "wheel", "setuptools", "build")
                session.run(
                    sys.executable, "-m", "pip", "wheel", ".",
                    "-w", "dist/", "--no-deps",
                    env=env, external=True
                )
                build_success = True
            except Exception as e2:
                session.log(f"Second attempt also failed: {e2}")

    # Install the project package to enable import
    if build_success:
        try:
            session.install("-e", ".")
            session.log("Successfully installed package in development mode")
        except Exception as e:
            session.log(f"Warning: Failed to install package in development mode: {e}")
            session.log("Continuing with process...")
    
    return build_success


def get_package_name():
    """Get the package name from the pyproject.toml file.
    
    Returns:
        str: The package name.
    """
    return MODULE_NAME


def get_package_version():
    """Get the package version from the pyproject.toml file.
    
    Returns:
        str: The package version.
    """
    try:
        import tomli
        with open(os.path.join(THIS_ROOT, "pyproject.toml"), "rb") as f:
            pyproject = tomli.load(f)
        return pyproject["project"]["version"]
    except (ImportError, FileNotFoundError, KeyError):
        try:
            # 尝试从 setup.py 中获取版本
            import re
            setup_py = os.path.join(THIS_ROOT, "setup.py")
            if os.path.exists(setup_py):
                with open(setup_py, "r") as f:
                    content = f.read()
                    version_match = re.search(r'version=["\']([^"\']+)["\']', content)
                    if version_match:
                        return version_match.group(1)
        except Exception:
            pass
        return "0.1.0"  # 默认版本


def check_doxygen_installed(session):
    """Check if Doxygen is installed and provide installation instructions if not.
    
    Args:
        session: Nox session object.
        
    Returns:
        bool: True if Doxygen is installed, False otherwise.
    """
    # Check if Doxygen is installed
    doxygen_installed = False

    if os.name == 'nt':  # Windows
        # First, check if there is a doxygen executable in the project directory
        local_doxygen = os.path.join(THIS_ROOT, "doxygen.exe")
        if os.path.exists(local_doxygen):
            doxygen_installed = True
        else:
            # Check if it is in the system path
            try:
                result = session.run("where", "doxygen", external=True, silent=True, success_codes=[0, 1])
                doxygen_installed = result == 0
            except Exception:
                doxygen_installed = False
    else:  # Linux/macOS
        try:
            result = session.run("which", "doxygen", external=True, silent=True, success_codes=[0, 1])
            doxygen_installed = result == 0
        except Exception:
            doxygen_installed = False

    if not doxygen_installed:
        session.log("Doxygen not found. C++ API documentation will not be generated.")
        session.log("Please install Doxygen manually:")
        if os.name == 'nt':  # Windows
            session.log("  1. Download from https://www.doxygen.nl/download.html")
            session.log("  2. Or run: choco install doxygen.install")

            # If the installer has been downloaded, prompt the user to run it
            if os.path.exists(os.path.join(THIS_ROOT, "doxygen-setup.exe")):
                session.log("  3. Or run the downloaded installer: doxygen-setup.exe")
        else:  # Linux/macOS
            if os.path.exists("/etc/debian_version"):  # Debian/Ubuntu
                session.log("  Run: sudo apt-get install -y doxygen")
            elif os.path.exists("/etc/redhat-release"):  # RHEL/CentOS/Fedora
                session.log("  Run: sudo yum install -y doxygen")
            elif os.path.exists("/etc/arch-release"):  # Arch Linux
                session.log("  Run: sudo pacman -S --noconfirm doxygen")
            elif os.path.exists("/usr/local/bin/brew"):  # macOS with Homebrew
                session.log("  Run: brew install doxygen")
            else:
                session.log("  Visit https://www.doxygen.nl/download.html")
    
    return doxygen_installed
