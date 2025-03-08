cmake_minimum_required(VERSION 3.15...3.30)
project(${SKBUILD_PROJECT_NAME} LANGUAGES CXX)

# 使用 scikit-build-core 的 FindPython 支持
find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)

# 如果 Python 版本是 3.7，输出一些调试信息
if(Python_VERSION MATCHES "^3\.7")
  message(STATUS "Found Python 3.7: ${Python_VERSION}")
  message(STATUS "  Python_EXECUTABLE: ${Python_EXECUTABLE}")
  message(STATUS "  Python_INCLUDE_DIRS: ${Python_INCLUDE_DIRS}")
  message(STATUS "  Python_LIBRARIES: ${Python_LIBRARIES}")
endif()

# Set C++ standard
set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Windows-specific configuration
if(WIN32)
    # Check if Ninja generator is being used
    if(CMAKE_GENERATOR MATCHES "Ninja")
        message(STATUS "Using Ninja generator")
    # Ensure we can find the compiler if using Visual Studio
    elseif(DEFINED ENV{VSCMD_ARG_TGT_ARCH})
        message(STATUS "Visual Studio environment detected: $ENV{VSCMD_ARG_TGT_ARCH}")
    else()
        message(STATUS "Using default build settings")
    endif()
    
    # Set Windows platform-specific configuration for MSVC
    if(MSVC)
      # Add MSVC-specific flags
      add_compile_options(/MP /bigobj)
      
      # Enable multi-threaded compilation
      set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /MP")
      
      # Set runtime library to match Python's expectations
      # Use Multi-threaded DLL runtime library (/MD) for Release builds
      set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} /MD")
      # Use Multi-threaded Debug DLL runtime library (/MDd) for Debug builds
      set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} /MDd")
      
      # 使用导出符号表文件
      set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS OFF)
      
      # 使用静态链接到Python库
      set(PYTHON_LINK_STATIC ON)
      
      # 检查是否指定了平台工具集
      if(NOT CMAKE_GENERATOR_TOOLSET)
        # Set the default toolset based on the Visual Studio version
        if(MSVC_VERSION GREATER_EQUAL 1920)
          # Visual Studio 2019 and above
          set(CMAKE_GENERATOR_TOOLSET "v142")
        elseif(MSVC_VERSION GREATER_EQUAL 1910)
          # Visual Studio 2017
          set(CMAKE_GENERATOR_TOOLSET "v141")
        elseif(MSVC_VERSION GREATER_EQUAL 1900)
          # Visual Studio 2015
          set(CMAKE_GENERATOR_TOOLSET "v140")
        endif()
      endif()
    endif()
endif()

# Disable some warnings
if(MSVC)
  # Disable warnings for MSVC
  add_compile_options(/W3 /wd4244 /wd4267 /wd4996 /wd4305)
else()
  # Disable warnings for GCC/Clang
  add_compile_options(-Wall -Wno-unused-variable -Wno-unused-but-set-variable -Wno-sign-compare -Wno-unused-parameter)
endif()

# Try to find NumPy
if(NOT Python_NumPy_FOUND)
    find_package(Python COMPONENTS NumPy QUIET)
    if(NOT Python_NumPy_FOUND AND Python_EXECUTABLE)
      # Try to find NumPy manually
      execute_process(
        COMMAND "${Python_EXECUTABLE}" -c "import numpy; print(numpy.get_include())"
        OUTPUT_VARIABLE Python_NumPy_INCLUDE_DIRS
        OUTPUT_STRIP_TRAILING_WHITESPACE
        ERROR_QUIET
        RESULT_VARIABLE _NUMPY_RESULT
      )
      if(_NUMPY_RESULT EQUAL 0 AND EXISTS "${Python_NumPy_INCLUDE_DIRS}")
        set(Python_NumPy_FOUND TRUE)
      endif()
    endif()
endif()

# Print debug information
message(STATUS "Python_EXECUTABLE: ${Python_EXECUTABLE}")
message(STATUS "Python_LIBRARIES: ${Python_LIBRARIES}")
message(STATUS "Python_INCLUDE_DIRS: ${Python_INCLUDE_DIRS}")
if(Python_NumPy_FOUND)
  message(STATUS "Python_NumPy_INCLUDE_DIRS: ${Python_NumPy_INCLUDE_DIRS}")
endif()

# Find pybind11
find_package(pybind11 CONFIG QUIET)
if(NOT pybind11_FOUND)
    # Try to find pybind11 using Python
    execute_process(
        COMMAND "${Python_EXECUTABLE}" -c "import pybind11; print(pybind11.get_include())"
        OUTPUT_VARIABLE PYBIND11_INCLUDE_DIR
        OUTPUT_STRIP_TRAILING_WHITESPACE
        RESULT_VARIABLE PYBIND11_IMPORT_RESULT
    )
    if(PYBIND11_IMPORT_RESULT EQUAL 0 AND EXISTS "${PYBIND11_INCLUDE_DIR}")
        message(STATUS "Found pybind11 include directory: ${PYBIND11_INCLUDE_DIR}")
        include_directories(${PYBIND11_INCLUDE_DIR})
        # Define pybind11 functions manually
        function(pybind11_add_module target_name)
            add_library(${target_name} MODULE ${ARGN})
            target_include_directories(${target_name} PRIVATE ${PYBIND11_INCLUDE_DIR})
            target_compile_definitions(${target_name} PRIVATE PYBIND11_DETAILED_ERROR_MESSAGES)
            
            # Use platform-specific extension
            if(WIN32)
                set_target_properties(${target_name} PROPERTIES PREFIX "" SUFFIX ".pyd")
                
                # 确保正确链接到Python库
                target_link_libraries(${target_name} PRIVATE ${Python_LIBRARIES})
                
                # 添加Windows特定的编译定义
                target_compile_definitions(${target_name} PRIVATE
                    _WINDOWS
                    NOMINMAX  # 避免min/max宏与STL冲突
                    WIN32_LEAN_AND_MEAN  # 减少Windows头文件包含
                )
            else()
                set_target_properties(${target_name} PROPERTIES PREFIX "" SUFFIX ".so")
            endif()
            
            # Ensure linking to the correct Python library
            if(WIN32)
                target_link_libraries(${target_name} PRIVATE ${Python_LIBRARIES})
            elseif(APPLE)
                # macOS may require special handling
                set_target_properties(${target_name} PROPERTIES LINK_FLAGS "-undefined dynamic_lookup")
            else()
                # Linux may require linking to the Python library
                if(NOT CMAKE_SYSTEM_NAME STREQUAL "Linux")
                    target_link_libraries(${target_name} PRIVATE ${Python_LIBRARIES})
                endif()
            endif()
        endfunction()
    else()
        message(FATAL_ERROR "Could not find pybind11. Please install it with pip install pybind11")
    endif()
endif()

# Find Eigen
find_package(Eigen3 QUIET)
if(NOT EIGEN3_FOUND)
    # Check if Eigen is available as a Git submodule
    if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/extern/eigen/Eigen/Core")
        message(STATUS "Using Eigen from Git submodule")
        set(EIGEN3_INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/extern/eigen")
        set(EIGEN3_FOUND TRUE)
    else()
        # Try to find Eigen3 using pkg-config
        find_package(PkgConfig QUIET)
        if(PKG_CONFIG_FOUND)
            pkg_check_modules(EIGEN3 QUIET eigen3)
        endif()

        # If still not found, try to use the Eigen from the Python package
        if(NOT EIGEN3_FOUND)
            message(STATUS "Eigen3 not found via find_package or pkg-config, trying Python package")
            execute_process(
                COMMAND "${Python_EXECUTABLE}" -c "import numpy; print(numpy.get_include())"
                OUTPUT_VARIABLE NUMPY_INCLUDE_DIR
                OUTPUT_STRIP_TRAILING_WHITESPACE
            )
            if(EXISTS "${NUMPY_INCLUDE_DIR}")
                set(EIGEN3_INCLUDE_DIR "${NUMPY_INCLUDE_DIR}/eigen3")
                if(NOT EXISTS "${EIGEN3_INCLUDE_DIR}")
                    message(FATAL_ERROR "Eigen3 not found. Please run 'git submodule update --init --recursive' to fetch the Eigen dependency.")
                endif()
            else()
                message(FATAL_ERROR "Eigen3 not found. Please run 'git submodule update --init --recursive' to fetch the Eigen dependency.")
            endif()
        endif()
    endif()
endif()

# OpenMP support
option(PY_DEM_BONES_USE_OPENMP "Use OpenMP for parallelization" ON)
if(PY_DEM_BONES_USE_OPENMP)
    find_package(OpenMP)
    if(OpenMP_CXX_FOUND)
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")
        set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} ${OpenMP_EXE_LINKER_FLAGS}")
    endif()
endif()

# Include directories
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/extern/dem-bones/include
    ${EIGEN3_INCLUDE_DIR}
)

if(Python_NumPy_FOUND)
    include_directories(${Python_NumPy_INCLUDE_DIRS})
endif()

# Add the pybind11 module
pybind11_add_module(_py_dem_bones 
    src/binding/py_dem_bones.cpp
    src/binding/py_dem_bones_ext.cpp
    src/binding/py_dem_bones_module.cpp
)

# Note: Do not directly define Py_LIMITED_API, as it will cause compilation errors in pybind11 internal classes and functions
# We temporarily remove ABI3 compatibility mode, as it is not compatible with the current pybind11 code

# Set target properties
set_target_properties(_py_dem_bones PROPERTIES
    OUTPUT_NAME "_py_dem_bones"
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/py_dem_bones"
)

# Windows-specific DLL handling
if(WIN32)
    # Copy required DLLs to the output directory
    # If using MSVC, copy the Visual C++ runtime DLL
    if(MSVC)
        # 使用静态库
        target_compile_options(_py_dem_bones PRIVATE 
            "/MT$<$<CONFIG:Debug>:d>"
        )
        
        # 关闭自动导出所有符号
        set_property(TARGET _py_dem_bones PROPERTY WINDOWS_EXPORT_ALL_SYMBOLS OFF)
        
        # 指定导出符号的宏定义
        target_compile_definitions(_py_dem_bones PRIVATE 
            "PYBIND11_EXPORT=__declspec(dllexport)"
        )
        
        # 指定导出符号表文件
        set_property(TARGET _py_dem_bones APPEND_STRING PROPERTY LINK_FLAGS 
            " /EXPORT:PyInit__py_dem_bones"
        )
    endif()
endif()

# Install the module - Ensure installation to the correct directory
install(TARGETS _py_dem_bones DESTINATION py_dem_bones)

# Copy Python files
file(GLOB PYTHON_FILES "${CMAKE_CURRENT_SOURCE_DIR}/src/py_dem_bones/*.py")
foreach(PYTHON_FILE ${PYTHON_FILES})
    get_filename_component(FILENAME ${PYTHON_FILE} NAME)
    configure_file(${PYTHON_FILE} "${CMAKE_CURRENT_BINARY_DIR}/py_dem_bones/${FILENAME}" COPYONLY)
endforeach()

# Set compiler options based on platform
if(MSVC)
    target_compile_definitions(_py_dem_bones PRIVATE WIN32 _WINDOWS)
    target_compile_options(_py_dem_bones PRIVATE
        /W3     # Warning level 3 (less strict than W4)
        /MP     # Multi-processor compilation
        /wd4244 # Disable warning C4244: conversion from 'double' to 'float'
        /wd4305 # Disable warning C4305: truncation from 'double' to 'float'
        /bigobj # Support for large object files
    )
elseif(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    target_compile_options(_py_dem_bones PRIVATE -Wall -Wextra -Wno-conversion)
else()
    target_compile_options(_py_dem_bones PRIVATE -Wall -Wextra -Wno-conversion)
endif()
