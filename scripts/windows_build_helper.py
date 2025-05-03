#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Windows Build Helper
===================

This script helps with Windows builds by:
1. Setting up the correct environment variables
2. Configuring Visual Studio tools
3. Running the build with optimized settings
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def find_vs_installation():
    """Find Visual Studio installation directory."""
    vs_paths = [
        r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Enterprise",
        r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Community",
        r"C:\Program Files\Microsoft Visual Studio\2022\Enterprise",
        r"C:\Program Files\Microsoft Visual Studio\2022\Community"
    ]
    
    for path in vs_paths:
        if os.path.exists(path):
            return path
    
    return None


def setup_vs_environment(arch="x64"):
    """Set up Visual Studio environment variables."""
    vs_path = find_vs_installation()
    if not vs_path:
        print("Visual Studio installation not found!")
        return False
    
    # Find vcvarsall.bat
    vcvarsall = os.path.join(vs_path, "VC", "Auxiliary", "Build", "vcvarsall.bat")
    if not os.path.exists(vcvarsall):
        print(f"vcvarsall.bat not found at {vcvarsall}")
        return False
    
    # Run vcvarsall.bat and capture environment variables
    cmd = f'"{vcvarsall}" {arch} && set'
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = process.communicate()
    
    if process.returncode != 0:
        print(f"Failed to run vcvarsall.bat: {stderr.decode()}")
        return False
    
    # Parse environment variables
    for line in stdout.decode().splitlines():
        if '=' in line:
            name, value = line.split('=', 1)
            os.environ[name] = value
    
    print(f"Visual Studio environment set up for {arch}")
    return True


def install_dependencies():
    """Install build dependencies."""
    print("Installing build dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ninja", "wheel", "setuptools", "numpy", "pybind11", "scikit-build-core", "cmake"])
    print("Dependencies installed successfully")


def build_wheel(build_dir="build", output_dir="dist"):
    """Build wheel package."""
    print("Building wheel package...")
    
    # Create build and output directories
    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    # Set environment variables for build
    os.environ["CMAKE_GENERATOR"] = "Ninja"
    os.environ["CMAKE_POSITION_INDEPENDENT_CODE"] = "ON"
    os.environ["CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS"] = "ON"
    
    # Build wheel
    cmd = [
        sys.executable, "-m", "pip", "wheel",
        "--no-deps",
        "--wheel-dir", output_dir,
        "--no-build-isolation",
        "."
    ]
    
    subprocess.check_call(cmd)
    print(f"Wheel built successfully in {output_dir}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Windows build helper for py-dem-bones")
    parser.add_argument("--arch", choices=["x64", "x86"], default="x64", help="Architecture to build for")
    parser.add_argument("--build-dir", default="build", help="Build directory")
    parser.add_argument("--output-dir", default="dist", help="Output directory for wheel")
    args = parser.parse_args()
    
    # Set up Visual Studio environment
    if not setup_vs_environment(args.arch):
        sys.exit(1)
    
    # Install dependencies
    install_dependencies()
    
    # Build wheel
    build_wheel(args.build_dir, args.output_dir)


if __name__ == "__main__":
    main()
