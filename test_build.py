"""
Test script to verify the build configuration.
This script attempts to build the package and run a simple import test.
"""

import os
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path


def run_command(cmd, cwd=None):
    """Run a command and return its output."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd, 
        cwd=cwd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        text=True,
        check=False
    )
    print(f"Return code: {result.returncode}")
    if result.stdout:
        print(f"STDOUT:\n{result.stdout}")
    if result.stderr:
        print(f"STDERR:\n{result.stderr}")
    return result


def test_build():
    """Test building the package."""
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    try:
        # Build the package
        build_result = run_command(
            [sys.executable, "-m", "pip", "install", "-e", "."],
            cwd=os.getcwd()
        )
        
        if build_result.returncode != 0:
            print("Build failed!")
            return False
        
        # Create a simple test script
        test_script = Path(temp_dir) / "test_import.py"
        with open(test_script, "w") as f:
            f.write("""
try:
    import py_dem_bones
    print(f"Successfully imported py_dem_bones version {py_dem_bones.__version__}")
    print("Module path:", py_dem_bones.__file__)
    # Try to import the C++ extension
    from py_dem_bones import DemBones
    print("Successfully imported DemBones class")
    # Create an instance
    db = DemBones()
    print("Successfully created DemBones instance")
    print("Test passed!")
    exit(0)
except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc()
    exit(1)
""")
        
        # Run the test script
        test_result = run_command([sys.executable, str(test_script)])
        
        if test_result.returncode != 0:
            print("Import test failed!")
            return False
        
        print("Build and import test successful!")
        return True
    
    finally:
        # Clean up
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    success = test_build()
    sys.exit(0 if success else 1)
