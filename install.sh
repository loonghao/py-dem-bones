#!/bin/bash
# Installation helper script for py-dem-bones on Linux and macOS

echo "Setting up environment for py-dem-bones..."

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected macOS system"
    OS_TYPE="macos"
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "Homebrew not found. We recommend installing it for better dependency management."
        echo "Visit https://brew.sh/ for installation instructions."
    else
        # Check for cmake
        if ! command -v cmake &> /dev/null; then
            echo "Installing CMake using Homebrew..."
            brew install cmake
        fi
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Detected Linux system"
    OS_TYPE="linux"
    
    # Check for cmake
    if ! command -v cmake &> /dev/null; then
        echo "CMake not found. Please install it using your package manager."
        echo "For example: sudo apt-get install cmake (Debian/Ubuntu) or sudo yum install cmake (CentOS/RHEL)"
        exit 1
    fi
else
    echo "Unsupported operating system: $OSTYPE"
    exit 1
fi

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Python 3 not found. Please install Python 3.7 or newer."
    exit 1
fi

# Install the package
echo "Installing py-dem-bones..."
python3 -m pip install -e .

if [ $? -ne 0 ]; then
    echo "Installation failed with error code $?"
    exit $?
fi

echo "Installation completed successfully!"
