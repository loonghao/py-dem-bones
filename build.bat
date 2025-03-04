@echo off
REM This script is maintained for backward compatibility
REM For more advanced features, use tools/wheels/build_windows_wheel.py directly

echo Building wheels using tools/wheels/build_windows_wheel.py...
python tools/wheels/build_windows_wheel.py
if %ERRORLEVEL% NEQ 0 (
    echo Build failed with error code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)

echo Build completed successfully. Wheel files are in the wheelhouse/ directory.
