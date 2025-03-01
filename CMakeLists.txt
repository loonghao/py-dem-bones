cmake_minimum_required(VERSION 3.15)
project(py_dem_bones VERSION 0.1.0 LANGUAGES CXX)

# Set C++ standard
set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Windows-specific configuration
if(WIN32)
    # Ensure we can find the compiler
    if(DEFINED ENV{VSCMD_ARG_TGT_ARCH})
        message(STATUS "Visual Studio environment detected: $ENV{VSCMD_ARG_TGT_ARCH}")
    else()
        message(STATUS "Visual Studio environment not detected, using default settings")
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

# Find Python
find_package(Python COMPONENTS Interpreter Development REQUIRED)
find_package(Python COMPONENTS NumPy QUIET)

# Find pybind11
find_package(pybind11 CONFIG)
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
            
            # 使用平台特定的扩展名
            if(WIN32)
                set_target_properties(${target_name} PROPERTIES PREFIX "" SUFFIX ".pyd")
            else()
                set_target_properties(${target_name} PROPERTIES PREFIX "" SUFFIX ".so")
            endif()
            
            if(WIN32)
                target_link_libraries(${target_name} PRIVATE ${Python_LIBRARIES})
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

# 注意：不要直接定义 Py_LIMITED_API，这会导致 pybind11 内部类和函数的编译错误
# 我们暂时移除 ABI3 兼容模式，因为它与当前的 pybind11 代码不兼容

# Set target properties
set_target_properties(_py_dem_bones PROPERTIES
    OUTPUT_NAME "_py_dem_bones"
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/py_dem_bones"
)

# Install the module - 确保安装到正确的目录
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
