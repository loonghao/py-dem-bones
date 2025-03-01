#!/usr/bin/env python
"""
统一的安装脚本，适用于所有平台（Windows、macOS 和 Linux）。
此脚本会自动检测操作系统，设置正确的环境，并安装 py-dem-bones 包。
"""

import os
import platform
import subprocess
import sys
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.absolute()


def find_vcvarsall():
    """查找 Windows 上的 vcvarsall.bat 文件。"""
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
    return None


def install_windows():
    """在 Windows 上安装包。"""
    print("正在 Windows 平台上安装...")

    # 查找 vcvarsall.bat
    vcvarsall = find_vcvarsall()
    if not vcvarsall:
        print("错误：找不到 Visual Studio 构建工具。")
        print("请安装 Visual Studio 2019 或 2022，并确保包含 C++ 构建工具。")
        return False

    print(f"找到 Visual Studio 环境：{vcvarsall}")

    # 创建批处理文件来设置环境并运行安装命令
    batch_file = PROJECT_ROOT / "temp_install.bat"
    with open(batch_file, "w") as f:
        f.write(f'call "{vcvarsall}" x64\n')
        f.write('set SKBUILD_CMAKE_VERBOSE=1\n')
        f.write('pip install -e .\n')

    # 运行批处理文件
    try:
        print("正在设置 Visual Studio 环境并安装...")
        subprocess.run(["cmd", "/c", str(batch_file)], check=True)
        success = True
    except subprocess.CalledProcessError as e:
        print(f"安装过程中出错：{e}")
        success = False
    finally:
        # 清理
        if batch_file.exists():
            batch_file.unlink()

    return success


def install_macos():
    """在 macOS 上安装包。"""
    print("正在 macOS 平台上安装...")

    # 检查 CMake 是否已安装
    try:
        subprocess.run(["cmake", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("警告：找不到 CMake。尝试使用 Homebrew 安装...")
        try:
            subprocess.run(["brew", "install", "cmake"], check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("错误：无法安装 CMake。请手动安装后重试。")
            return False

    # 设置环境变量并安装
    env = os.environ.copy()
    env["SKBUILD_CMAKE_VERBOSE"] = "1"

    try:
        print("正在安装 py-dem-bones...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], check=True, env=env)
        return True
    except subprocess.CalledProcessError as e:
        print(f"安装过程中出错：{e}")
        return False


def install_linux():
    """在 Linux 上安装包。"""
    print("正在 Linux 平台上安装...")

    # 检查 CMake 是否已安装
    try:
        subprocess.run(["cmake", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("错误：找不到 CMake。请使用包管理器安装 CMake 后重试。")
        print("例如：sudo apt-get install cmake（Debian/Ubuntu）或 sudo yum install cmake（CentOS/RHEL）")
        return False

    # 设置环境变量并安装
    env = os.environ.copy()
    env["SKBUILD_CMAKE_VERBOSE"] = "1"

    try:
        print("正在安装 py-dem-bones...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], check=True, env=env)
        return True
    except subprocess.CalledProcessError as e:
        print(f"安装过程中出错：{e}")
        return False


def main():
    """主函数，检测平台并执行相应的安装过程。"""
    print("py-dem-bones 安装脚本")
    print("=====================")

    # 检测操作系统
    system = platform.system()

    # 确保 pip 已安装
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("错误：找不到 pip。请确保 pip 已安装。")
        return 1

    # 根据平台执行相应的安装过程
    if system == "Windows":
        success = install_windows()
    elif system == "Darwin":  # macOS
        success = install_macos()
    elif system == "Linux":
        success = install_linux()
    else:
        print(f"错误：不支持的操作系统：{system}")
        return 1

    if success:
        print("\n安装成功！")
        print("您可以通过以下方式导入 py-dem-bones：")
        print("  import py_dem_bones")
        return 0
    else:
        print("\n安装失败。请查看上面的错误信息。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
