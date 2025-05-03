#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Windows Build Debug Script
==========================

This script helps diagnose Windows build issues by:
1. Checking the environment
2. Verifying Visual Studio installation
3. Testing CMake configuration
4. Checking Python and package versions
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path


def print_section(title):
    """Print a section title."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)


def run_command(cmd, cwd=None):
    """Run a command and return its output."""
    try:
        result = subprocess.run(
            cmd, 
            cwd=cwd, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, f"Error: {e}\nStdout: {e.stdout}\nStderr: {e.stderr}"
    except Exception as e:
        return False, f"Error: {e}"


def check_environment():
    """Check the environment variables."""
    print_section("Environment Variables")
    
    # Check important environment variables
    important_vars = [
        "PATH", "PYTHONPATH", "CMAKE_PREFIX_PATH", "INCLUDE", "LIB",
        "VSCMD_ARG_TGT_ARCH", "VCToolsRedistDir", "VCINSTALLDIR"
    ]
    
    for var in important_vars:
        value = os.environ.get(var, "Not set")
        if var == "PATH":
            print(f"{var}:")
            for path in value.split(os.pathsep):
                print(f"  - {path}")
        else:
            print(f"{var}: {value}")


def check_visual_studio():
    """Check Visual Studio installation."""
    print_section("Visual Studio Installation")
    
    # Check for Visual Studio installation
    vs_paths = [
        r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Enterprise",
        r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Community",
        r"C:\Program Files\Microsoft Visual Studio\2022\Enterprise",
        r"C:\Program Files\Microsoft Visual Studio\2022\Community"
    ]
    
    for path in vs_paths:
        if os.path.exists(path):
            print(f"Found Visual Studio at: {path}")
            
            # Check for VC tools
            vc_tools = os.path.join(path, "VC", "Tools", "MSVC")
            if os.path.exists(vc_tools):
                versions = os.listdir(vc_tools)
                print(f"Found VC tools versions: {', '.join(versions)}")
            else:
                print(f"VC tools not found at: {vc_tools}")
            
            break
    else:
        print("Visual Studio not found in standard locations")
    
    # Check for cl.exe
    cl_exe = shutil.which("cl")
    if cl_exe:
        print(f"Found cl.exe at: {cl_exe}")
        success, output = run_command(["cl", "/?"])
        if success:
            version_line = output.splitlines()[0]
            print(f"cl.exe version: {version_line}")
        else:
            print(f"Failed to get cl.exe version: {output}")
    else:
        print("cl.exe not found in PATH")


def check_cmake():
    """Check CMake installation and configuration."""
    print_section("CMake Installation")
    
    # Check for CMake
    cmake_exe = shutil.which("cmake")
    if cmake_exe:
        print(f"Found CMake at: {cmake_exe}")
        success, output = run_command(["cmake", "--version"])
        if success:
            print(f"CMake version: {output.splitlines()[0]}")
        else:
            print(f"Failed to get CMake version: {output}")
        
        # Check CMake generators
        success, output = run_command(["cmake", "--help"])
        if success:
            generators = []
            in_generators_section = False
            for line in output.splitlines():
                if "Generators" in line:
                    in_generators_section = True
                    continue
                if in_generators_section and line.strip().startswith("*"):
                    generators.append(line.strip())
            
            print("Available CMake generators:")
            for gen in generators:
                print(f"  {gen}")
        else:
            print(f"Failed to get CMake generators: {output}")
    else:
        print("CMake not found in PATH")


def check_python():
    """Check Python installation and packages."""
    print_section("Python Installation")
    
    # Print Python version info
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Python path: {sys.path}")
    
    # Check for important packages
    packages = [
        "numpy", "pybind11", "scikit-build-core", "cmake", "wheel", 
        "setuptools", "pip", "pytest"
    ]
    
    print("\nInstalled packages:")
    for package in packages:
        try:
            module = __import__(package)
            version = getattr(module, "__version__", "unknown")
            print(f"  {package}: {version}")
        except ImportError:
            print(f"  {package}: Not installed")


def check_ninja():
    """Check Ninja installation."""
    print_section("Ninja Installation")
    
    # Check for Ninja
    ninja_exe = shutil.which("ninja")
    if ninja_exe:
        print(f"Found Ninja at: {ninja_exe}")
        success, output = run_command(["ninja", "--version"])
        if success:
            print(f"Ninja version: {output.strip()}")
        else:
            print(f"Failed to get Ninja version: {output}")
    else:
        print("Ninja not found in PATH")


def main():
    """Main function."""
    print_section("Windows Build Debug Information")
    print(f"Date: {subprocess.check_output('date /t', shell=True).decode().strip()}")
    print(f"Time: {subprocess.check_output('time /t', shell=True).decode().strip()}")
    print(f"System: {platform.system()} {platform.release()} {platform.version()}")
    print(f"Architecture: {platform.machine()}")
    print(f"Processor: {platform.processor()}")
    
    # Run checks
    check_environment()
    check_visual_studio()
    check_cmake()
    check_ninja()
    check_python()
    
    print_section("Debug Complete")
    print("If you're experiencing build issues, please include this output in your bug report.")


if __name__ == "__main__":
    main()
