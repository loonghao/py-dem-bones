# Copyright Contributors to the py-dem-bones project.
# SPDX-License-Identifier: BSD-3-Clause

# This module enables ccache for faster builds if it's found on the system.
# It will be silently ignored if ccache is not found.

option(USE_CCACHE "Use ccache if found" ON)

if(USE_CCACHE)
    find_program(CCACHE_FOUND ccache)
    if(CCACHE_FOUND)
        message(STATUS "Using ccache: ${CCACHE_FOUND}")
        # Set up wrapper scripts
        set_property(GLOBAL PROPERTY RULE_LAUNCH_COMPILE ccache)
        set_property(GLOBAL PROPERTY RULE_LAUNCH_LINK ccache)
        
        # Set ccache config options
        # Unlimited cache size
        set(ENV{CCACHE_MAXSIZE} "0")
        # Cache results for up to 2 weeks
        set(ENV{CCACHE_SLOPPINESS} "pch_defines,time_macros")
        # Use compression
        set(ENV{CCACHE_COMPRESS} "1")
        
        # Set up for different platforms
        if(WIN32)
            # Windows-specific ccache settings
            set(ENV{CCACHE_BASEDIR} "${CMAKE_SOURCE_DIR}")
        elseif(APPLE)
            # macOS-specific ccache settings
            set(ENV{CCACHE_CPP2} "yes")
        endif()
    else()
        message(STATUS "ccache not found, builds will not be accelerated")
    endif()
endif()
