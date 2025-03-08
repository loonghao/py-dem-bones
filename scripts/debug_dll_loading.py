#!/usr/bin/env python
"""
Debug DLL loading issues for py_dem_bones package.

This script attempts to manually load the _py_dem_bones extension module
and its dependencies to diagnose DLL loading problems.
"""
import os
import sys
import site
import ctypes
import glob
import importlib.util
from ctypes import windll, c_buffer, byref, sizeof, c_ulong


def get_dll_dependencies(dll_path):
    """Get the dependencies of a DLL file using Windows API."""
    if not os.path.exists(dll_path):
        print(f"Error: File not found: {dll_path}")
        return []
    
    try:
        # Load the DLL
        dll = windll.kernel32.LoadLibraryExW(dll_path, 0, 0)
        if not dll:
            print(f"Error: Failed to load DLL: {dll_path}")
            return []
        
        # Get the module information
        module_info = c_buffer(256)
        windll.kernel32.GetModuleFileNameW(dll, module_info, sizeof(module_info))
        
        # Unload the DLL
        windll.kernel32.FreeLibrary(dll)
        
        # Get the dependencies
        dependencies = []
        # This is a simplified approach - in reality, you would need to parse the PE headers
        # to get the actual dependencies
        
        return dependencies
    except Exception as e:
        print(f"Error analyzing DLL: {e}")
        return []


def find_dll(dll_name):
    """Find a DLL in the system path."""
    # Check in the current directory
    if os.path.exists(dll_name):
        return os.path.abspath(dll_name)
    
    # Check in the Python directory
    python_dir = os.path.dirname(sys.executable)
    python_dll_path = os.path.join(python_dir, dll_name)
    if os.path.exists(python_dll_path):
        return python_dll_path
    
    # Check in the Python DLLs directory
    python_dlls_dir = os.path.join(python_dir, "DLLs")
    python_dlls_path = os.path.join(python_dlls_dir, dll_name)
    if os.path.exists(python_dlls_path):
        return python_dlls_path
    
    # Check in site-packages
    for site_pkg in site.getsitepackages():
        site_pkg_dll_path = os.path.join(site_pkg, dll_name)
        if os.path.exists(site_pkg_dll_path):
            return site_pkg_dll_path
    
    # Check in the PATH
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    for path_dir in path_dirs:
        path_dll = os.path.join(path_dir, dll_name)
        if os.path.exists(path_dll):
            return path_dll
    
    # Check in Windows system directories
    system_dirs = [
        os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32"),
        os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "SysWOW64"),
    ]
    for system_dir in system_dirs:
        system_dll_path = os.path.join(system_dir, dll_name)
        if os.path.exists(system_dll_path):
            return system_dll_path
    
    return None


def find_py_dem_bones_extension():
    """Find the _py_dem_bones extension module."""
    # Look in site-packages
    for site_pkg in site.getsitepackages():
        py_dem_bones_dir = os.path.join(site_pkg, "py_dem_bones")
        if os.path.exists(py_dem_bones_dir):
            # Look for .pyd file
            pyd_files = glob.glob(os.path.join(py_dem_bones_dir, "_py_dem_bones*.pyd"))
            if pyd_files:
                return pyd_files[0]
    
    return None


def check_vc_redist():
    """Check if Visual C++ Redistributable is installed."""
    try:
        # Try to load a common VC++ Redist DLL
        ctypes.WinDLL("msvcp140.dll")
        print("Visual C++ Redistributable appears to be installed (msvcp140.dll found)")
        return True
    except Exception:
        print("WARNING: Visual C++ Redistributable may not be installed (msvcp140.dll not found)")
        print("Please install the Visual C++ Redistributable for Visual Studio 2015-2022")
        return False


def debug_py_dem_bones_loading():
    """Debug the loading of py_dem_bones module."""
    print("\n=== Python Environment Information ===")
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"sys.path: {sys.path}")
    
    # Check for Visual C++ Redistributable
    print("\n=== Checking for Visual C++ Redistributable ===")
    check_vc_redist()
    
    # Find the extension module
    print("\n=== Finding py_dem_bones Extension Module ===")
    extension_path = find_py_dem_bones_extension()
    if extension_path:
        print(f"Found extension module at: {extension_path}")
        
        # Try to load the extension with ctypes
        print("\n=== Attempting to Load Extension with ctypes ===")
        try:
            ext_dll = ctypes.CDLL(extension_path)
            print(f"Successfully loaded extension with ctypes: {ext_dll}")
        except Exception as e:
            print(f"Failed to load extension with ctypes: {e}")
            
            # Try to get the Windows error code
            error_code = ctypes.GetLastError()
            print(f"Windows error code: {error_code}")
            
            # Check for common DLLs
            print("\n=== Checking for Common DLLs ===")
            common_dlls = [
                "msvcp140.dll",  # Visual C++ 2015-2022 Redistributable
                "vcruntime140.dll",  # Visual C++ 2015-2022 Redistributable
                "vcruntime140_1.dll",  # Visual C++ 2015-2022 Redistributable
                "python3.dll",  # Python DLL
                "python310.dll",  # Python 3.10 DLL (adjust for your Python version)
            ]
            
            for dll in common_dlls:
                dll_path = find_dll(dll)
                if dll_path:
                    print(f"Found {dll} at: {dll_path}")
                else:
                    print(f"WARNING: Could not find {dll}")
    else:
        print("Could not find py_dem_bones extension module")
    
    # Try normal import
    print("\n=== Attempting Normal Import ===")
    try:
        import py_dem_bones
        print(f"Successfully imported py_dem_bones {py_dem_bones.__version__}")
        print(f"Module location: {py_dem_bones.__file__}")
    except ImportError as e:
        print(f"Error importing py_dem_bones: {e}")
    
    print("\n=== Debug Complete ===")


if __name__ == "__main__":
    debug_py_dem_bones_loading()
