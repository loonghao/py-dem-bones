"""
Copy static files to the build directory.
This script is used to ensure that all static files are correctly copied to the build directory.
"""
import os
import shutil
from pathlib import Path


def copy_static_files(source_dir="_static", target_dir="_build/html/_static"):
    """Copy all files from source_dir to target_dir.
    
    Args:
        source_dir: Source directory path (relative to docs directory)
        target_dir: Target directory path (relative to docs directory)
    """
    # Get the current directory (should be the docs directory)
    current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    
    # Get the source and target directories
    source_path = current_dir / source_dir
    target_path = current_dir / target_dir
    
    # Create the target directory if it doesn't exist
    os.makedirs(target_path, exist_ok=True)
    
    # Copy all files from source to target
    if source_path.exists():
        print(f"Copying files from {source_path} to {target_path}")
        file_count = 0
        for file in source_path.glob("*"):
            if file.is_file():
                try:
                    shutil.copy2(file, target_path)
                    print(f"  Copied {file.name}")
                    file_count += 1
                except Exception as e:
                    print(f"  Failed to copy {file.name}: {e}")
        print(f"Copied {file_count} files")
    else:
        print(f"Source directory {source_path} does not exist")


if __name__ == "__main__":
    copy_static_files()
