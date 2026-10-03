# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.13.0](https://github.com/loonghao/py-dem-bones/compare/0.12.4...v0.13.0) (2026-10-03)


### Features

* add detailed native render studies ([2184abd](https://github.com/loonghao/py-dem-bones/commit/2184abd6ae846d22a87d18cea97b47447fd94241))
* add licensed octopus materials and native SSS study ([46502c0](https://github.com/loonghao/py-dem-bones/commit/46502c0ea6e15f3ea65c02de4cb7e2823a279a64))
* add native DCC skinning showcase and provenance ([f2d3717](https://github.com/loonghao/py-dem-bones/commit/f2d3717ca5c39fa232c8e4e6d91d636378c1b37c))
* add portable DCC skinning and release-please ([108765c](https://github.com/loonghao/py-dem-bones/commit/108765c24f32b44a195b9758f760f9dced6c0f56))
* complete native Mantra motion showcase ([f8bb59b](https://github.com/loonghao/py-dem-bones/commit/f8bb59b430866784ca9cd82c1da80f289e633948))
* migrate DCC adapters to shared skinning contracts ([b57df51](https://github.com/loonghao/py-dem-bones/commit/b57df51a8329c7fbc3c316f0bead0060017a71ef))
* publish native Mantra and Unreal SSS showcases ([2af3601](https://github.com/loonghao/py-dem-bones/commit/2af3601aaddb6c7ed36768614bbd43e9f0a84ea2))
* showcase native octopus softbody reconstruction ([861943d](https://github.com/loonghao/py-dem-bones/commit/861943d96e357ee2ab2f0e15ea3f574183be614c))


### Bug Fixes

* **ci:** repair release-please to release publish chain ([#92](https://github.com/loonghao/py-dem-bones/issues/92)) ([6423701](https://github.com/loonghao/py-dem-bones/commit/642370117b7581e29ab08799c9c38926ca186b4b))
* **ci:** repair repo-level CI failures blocking every PR ([1e70b13](https://github.com/loonghao/py-dem-bones/commit/1e70b13c679db305c121e52033d4c516119cc395))
* fetch pinned Eigen from the official mirror ([52aeb05](https://github.com/loonghao/py-dem-bones/commit/52aeb0537c2e4043ad8eb036028462edcf57177c))
* preserve all native transformation blocks ([0b0a05c](https://github.com/loonghao/py-dem-bones/commit/0b0a05c947c098021ec82df3f864e08c0c4bfd42))
* preserve exact showcase bytes across platforms ([d2daa81](https://github.com/loonghao/py-dem-bones/commit/d2daa81e2fb70072a0d1f9fb8950ccf05c981dee))
* refresh packed skin textures and publish SSS comparison ([f3be53a](https://github.com/loonghao/py-dem-bones/commit/f3be53a9135680affd2f8629664bc6d5f1988a38))


### Documentation

* align RBF examples with adapter lifecycle ([9c4c28a](https://github.com/loonghao/py-dem-bones/commit/9c4c28a54cf179ba8e3eb6a39ea590c644a64cf1))
* correct RBF section headings ([d442515](https://github.com/loonghao/py-dem-bones/commit/d442515cf6513426a688ab30eb2b818f52567dd7))

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
