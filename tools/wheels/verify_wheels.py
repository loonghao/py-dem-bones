#!/usr/bin/env python
"""
Verify the platform tags of wheel files to ensure they comply with PyPI requirements.
"""

import os
import sys
import glob
from wheel.cli import tags as wheel_tags


def verify_wheels(wheel_dir=None):
    """Verify the platform tags of wheel files.
    
    Args:
        wheel_dir: Directory containing wheel files. If None, uses wheelhouse and dist directories.
    
    Returns:
        bool: True if all wheel files have valid platform tags, False otherwise.
    """
    if wheel_dir:
        wheel_dirs = [wheel_dir]
    else:
        wheel_dirs = ["wheelhouse", "dist"]
    
    wheels = []
    for dir_name in wheel_dirs:
        if os.path.exists(dir_name):
            wheels.extend(glob.glob(os.path.join(dir_name, "*.whl")))
    
    if not wheels:
        print("No wheel files found!")
        return False
    
    all_valid = True
    
    print(f"Found {len(wheels)} wheel files:")
    for wheel in wheels:
        print(f"\nChecking wheel file: {os.path.basename(wheel)}")
        try:
            # Use wheel.cli.tags module to get the tags of the wheel file
            wheel_tags.tags(wheel)
            print("✅ Platform tags valid")
        except Exception as e:
            print(f"❌ Platform tags invalid: {e}")
            all_valid = False
    
    return all_valid


if __name__ == "__main__":
    wheel_dir = sys.argv[1] if len(sys.argv) > 1 else None
    success = verify_wheels(wheel_dir)
    sys.exit(0 if success else 1)
