@echo off
REM Windows installation helper script for py-dem-bones
REM This script sets up the Visual Studio environment and runs pip install

echo Setting up Visual Studio environment...

REM Try to find vcvarsall.bat
set VCVARSALL_FOUND=0

REM Visual Studio 2022 paths
if exist "C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" (
    set VCVARSALL="C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat"
    set VCVARSALL_FOUND=1
) else if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat" (
    set VCVARSALL="C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat"
    set VCVARSALL_FOUND=1
) else if exist "C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvarsall.bat" (
    set VCVARSALL="C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvarsall.bat"
    set VCVARSALL_FOUND=1
) else if exist "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvarsall.bat" (
    set VCVARSALL="C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvarsall.bat"
    set VCVARSALL_FOUND=1
)

REM Visual Studio 2019 paths
if %VCVARSALL_FOUND%==0 (
    if exist "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" (
        set VCVARSALL="C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvarsall.bat"
        set VCVARSALL_FOUND=1
    ) else if exist "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvarsall.bat" (
        set VCVARSALL="C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvarsall.bat"
        set VCVARSALL_FOUND=1
    ) else if exist "C:\Program Files (x86)\Microsoft Visual Studio\2019\Professional\VC\Auxiliary\Build\vcvarsall.bat" (
        set VCVARSALL="C:\Program Files (x86)\Microsoft Visual Studio\2019\Professional\VC\Auxiliary\Build\vcvarsall.bat"
        set VCVARSALL_FOUND=1
    ) else if exist "C:\Program Files (x86)\Microsoft Visual Studio\2019\Enterprise\VC\Auxiliary\Build\vcvarsall.bat" (
        set VCVARSALL="C:\Program Files (x86)\Microsoft Visual Studio\2019\Enterprise\VC\Auxiliary\Build\vcvarsall.bat"
        set VCVARSALL_FOUND=1
    )
)

if %VCVARSALL_FOUND%==0 (
    echo ERROR: Could not find Visual Studio Build Tools.
    echo Please install Visual Studio 2019/2022 with C++ build tools.
    exit /b 1
)

echo Found Visual Studio at %VCVARSALL%
echo Setting up environment for x64 architecture...

REM Set up Visual Studio environment for x64
call %VCVARSALL% x64

REM Install the package
echo Installing py-dem-bones...
pip install -e .

if %ERRORLEVEL% NEQ 0 (
    echo Installation failed with error code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)

echo Installation completed successfully!
