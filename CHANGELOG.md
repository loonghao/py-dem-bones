# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 0.12.4 (2025-05-05)

### Fix

- remove setuptools-scm version file generation

## 0.12.3 (2025-05-05)

### Fix

- resolve metadata version mismatch in build process
- add -- separator for commitizen version arguments to prevent parsing errors

## 0.12.2 (2025-05-05)

### Fix

- auto bump version

## 0.12.1 (2025-05-05)

### Fix

- unify isort and ruff configurations to fix lint issues
- update commitizen and setuptools_scm configuration
- remove changelog_increment_filename parameter
- simplify version management using commitizen github action
- update commitizen configuration to match official documentation
- integrate commitizen for unified version management
- resolve build warnings and metadata mismatch issues

## 0.12.0 (2025-05-05)

### Fix

- remove main branch push trigger from release workflow to prevent duplicate builds

## 0.11.1 (2025-05-05)

### Fix

- unify version management and prevent multiple workflow triggers
- update setuptools_scm.dump_version call in release.yml

## 0.11.0 (2025-05-05)

### Fix

- prevent multiple workflow triggers on version updates

## 0.10.1 (2025-05-05)

## 0.10.0 (2025-05-05)

## 0.9.1 (2025-05-05)

## 0.9.0 (2025-05-05)

### Fix

- improve version update process in CI
- add root parameter to setuptools_scm.dump_version call
- update setuptools_scm.dump_version call with correct parameters
- resolve line length lint error in base.py
- resolve version mismatch in build process

### Refactor

- remove duplicate version configuration

## 0.8.1 (2025-05-04)

### Feat

- improve Windows build support with cibuildwheel
- optimize py_dem_bones code with enhanced functionality

### Fix

- Fix target_vertices_operations test by improving set_target_name method
- Fix remaining unit test failures
- Improve ccache configuration for better CI performance
- Fix three failing unit tests
- prevent segmentation faults in get_weights
- prevent segmentation faults in get_weights
- resolve test failures
- resolve build and test issues
- add ssize_t definition for Windows compatibility
- resolve isort linting issues and CMake warnings
- use std::vector<ssize_t> for array shape to avoid ambiguity
- ensure empty arrays have correct shape to avoid segfault
- resolve ambiguous array_t constructor calls in binding code
- add version file generation to pyproject.toml
- correct setuptools_scm provider in pyproject.toml
- correct setuptools_scm provider in pyproject.toml
- enable experimental features in scikit-build-core
- replace bare except with specific exception handling
- ensure consistent version handling with setuptools_scm

## 0.8.0 (2025-05-04)

### Feat

- optimize GitHub Actions workflow with reusable components
- implement parallel build-and-test workflow
- use nox pytest_skip_install session for all tests
- implement parallel testing for each build
- optimize cibuildwheel build process with parallel jobs

### Fix

- update __dem_bones_version__ to match official version 1.2.1
- add __dem_bones_version__ to C++ module and update imports
- add hardcoded __dem_bones_version__ to version file
- add __dem_bones_version__ to version file
- update setuptools_scm configuration to fix build errors
- remove unsupported tag_format parameter from setuptools_scm config
- use setuptools_scm version_file for version generation
- move setuptools_scm config to its own section
- simplify TOML format for better compatibility
- quote hyphenated keys in TOML
- correct generate configuration format in pyproject.toml
- correct generate configuration in pyproject.toml
- optimize version configuration using setuptools_scm
- update version format to not use 'v' prefix
- restore scikit-build-core and implement dynamic version updates

## 0.7.0 (2025-05-03)

### Feat

- add ccache support to accelerate builds
- add coverage function to nox_actions/codetest.py
- add test coverage reporting
- enhance test suite and CI configuration
- remove Python 3.7 support and fix Windows build issues

### Fix

- improve cibuildwheel configuration based on OpenColorIO
- improve Windows build configuration
- simplify scikit-build configuration to fix parsing errors
- **deps**: update dependency black to v25

## 0.6.7 (2025-05-03)

### Fix

- **deps**: update dependency isort to v6

## 0.6.6 (2025-03-08)

### Refactor

- update version and fix auto tag version

## 0.6.5 (2025-03-08)

### Fix

- improve Windows compatibility and testing
- improve Windows DLL handling and compatibility
- improve Windows compatibility and testing

### Refactor

- Update version numbers and release config

## 0.6.4 (2025-03-08)

### Refactor

- **release**: Add tag filtering

## 0.6.3 (2025-03-06)

### Refactor

- Update version numbers and simplify configurations

## 0.6.2 (2025-03-06)

### Fix

- **deps**: update dependency numpy to >=1.26.4,<1.27.0

## 0.6.1 (2025-03-06)

### Fix

- **deps**: update dependency commitizen to v4

## 0.6.0 (2025-03-06)

### Feat

- Upgrade project setup and integrate SciPy RBF

## 0.5.1 (2025-03-06)

### Fix

- update dem-bones submodule to use master branch

### Refactor

- Update configs and workflows

## 0.5.0 (2025-03-05)

### Feat

- Add RBF interpolation examples and update docs

## 0.4.1 (2025-03-05)

### Refactor

- Update version numbers and configurations

## 0.4.0 (2025-03-05)

### Feat

- Update project version and workflow

### Refactor

- Improve code formatting and type hints
- Improve code formatting and type hints

## 0.3.0 (2025-03-04)

### Feat

- Integrate cibuildwheel for multi-platform wheel building

### Fix

- prevent duplicate CI triggers and improve release workflow

## v0.2.1 (2025-03-03)

### Refactor

- add more examples

## v0.2.0 (2025-03-03)

### Feat

- Update version and expand documentation

## v0.1.0 (2025-03-03)

### Added
- Update project setup and add utilities
- Initial project structure
- Core bindings for DemBones and DemBonesExt
- Python wrapper classes for easier integration
- Basic NumPy integration
- Documentation framework
- Testing framework
- Cross-platform support (Windows, Linux, macOS)
- CI/CD pipeline with GitHub Actions

## v0.0.1 (2025-02-22)

### Added
- Initial repository setup
