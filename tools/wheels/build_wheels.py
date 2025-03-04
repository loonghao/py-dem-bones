#!/usr/bin/env python
"""
构建 wheel 包的工具脚本。

此脚本使用 cibuildwheel 为当前平台构建 wheel 包。
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, cwd=None):
    """运行命令并返回输出。"""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        print(result.stdout)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(e.stdout)
        return False, e.stdout


def install_dependencies():
    """安装构建依赖。"""
    print("Installing dependencies...")
    deps = ["cibuildwheel", "wheel", "build", "twine"]
    success, _ = run_command([sys.executable, "-m", "pip", "install", "-U"] + deps)
    return success


def build_wheels():
    """使用 cibuildwheel 构建 wheel 包。"""
    print("Building wheels...")
    env = os.environ.copy()
    env["CIBW_BUILD_VERBOSITY"] = "3"
    
    # 使用 cibuildwheel 构建 wheel
    success, _ = run_command(
        [sys.executable, "-m", "cibuildwheel", "--platform", "auto"],
        cwd=str(Path(__file__).parent.parent.parent),  # 项目根目录
        env=env,
    )
    
    if not success:
        print("Failed to build wheels with cibuildwheel. Trying with build...")
        # 如果 cibuildwheel 失败，尝试使用 build
        success, _ = run_command(
            [sys.executable, "-m", "build", "--wheel", "--no-isolation", "--outdir", "dist/"],
            cwd=str(Path(__file__).parent.parent.parent),
        )
    
    return success


def verify_wheels():
    """验证构建的 wheel 包。"""
    print("Verifying wheels...")
    wheelhouse = Path(__file__).parent.parent.parent / "wheelhouse"
    if not wheelhouse.exists():
        wheelhouse = Path(__file__).parent.parent.parent / "dist"
    
    if not wheelhouse.exists() or not list(wheelhouse.glob("*.whl")):
        print("No wheels found!")
        return False
    
    print(f"Found wheels in {wheelhouse}:")
    for wheel in wheelhouse.glob("*.whl"):
        print(f"  - {wheel.name}")
    
    # 验证 wheel 标签
    for wheel in wheelhouse.glob("*.whl"):
        success, output = run_command([sys.executable, "-m", "wheel", "tags", str(wheel)])
        if not success:
            return False
    
    return True


def main():
    """主函数。"""
    print("=" * 80)
    print("Building wheels for py-dem-bones")
    print("=" * 80)
    
    # 安装依赖
    if not install_dependencies():
        print("Failed to install dependencies.")
        return 1
    
    # 构建 wheel
    if not build_wheels():
        print("Failed to build wheels.")
        return 1
    
    # 验证 wheel
    if not verify_wheels():
        print("Failed to verify wheels.")
        return 1
    
    print("=" * 80)
    print("Wheel build completed successfully!")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
