CI/CD Pipeline
=============

This project uses GitHub Actions for continuous integration and deployment. The CI/CD pipeline is designed to be efficient and reliable, with optimizations for faster builds and reduced resource consumption.

Workflow Overview
-----------------

The CI/CD pipeline consists of several workflows:

- **Main Workflow** (``main.yml``): Triggered on push to main branch, pull requests, and manual dispatch. Handles building and testing the package on multiple platforms and Python versions.
- **Release Workflow** (``release.yml``): Triggered on release creation. Builds and publishes the package to PyPI.
- **Bump Version Workflow** (``bumpversion.yml``): Automates version bumping.
- **Reusable Jobs** (``reusable-jobs.yml``): Contains reusable job definitions for build, test, lint, docs, and release tasks.

Optimization Strategies
-----------------------

The CI/CD pipeline implements several optimization strategies:

Reduced Build Matrix
~~~~~~~~~~~~~~~~~~~~

- Main testing focuses on the latest stable Python version (3.11) across all platforms
- Other Python versions are primarily tested on Linux to reduce unnecessary cross-platform testing
- Fast mode option allows running only critical test combinations during manual triggers

Caching Mechanism
~~~~~~~~~~~~~~~~~

- Pip dependencies are cached using ``pyproject.toml`` as the cache key
- Eigen library is cached to avoid repeated downloads and installations
- Utilizes the built-in caching functionality of ``actions/setup-python``

Optimized Checkout Process
~~~~~~~~~~~~~~~~~~~~~~~~~~

- Reduced git checkout depth (``fetch-depth: 1``) for faster checkout
- Optimized submodule initialization process
- SSH URLs are replaced with HTTPS URLs for better compatibility with GitHub Actions

Smart Step Skipping
~~~~~~~~~~~~~~~~~~~

- Conditional checks to avoid reinstalling already cached Eigen library
- Fast mode option in release workflow to skip unnecessary builds during development testing

Concurrency Control
~~~~~~~~~~~~~~~~

- Concurrency groups and cancellation of in-progress tasks to avoid duplicate runs and resource waste

Troubleshooting Common Issues
------------------------------

Git Submodules Initialization Failure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptom**: "Eigen not found" error during build

**Solution**:
- Ensure checkout step includes ``with: submodules: recursive``
- Add proper URL replacement configuration:

.. code-block:: yaml

    - name: Initialize git submodules
      shell: bash
      run: |
        git config --global url.https://github.com/.insteadOf git@github.com:
        git config --global url.https://.insteadOf git://
        git submodule sync
        git submodule update --init --recursive

Command Execution Issues
~~~~~~~~~~~~~~~~~~~~~

**Symptom**: ``uvx: command not found`` errors

**Solution**:
  - Use ``python -m`` commands instead of tool-specific commands:
    - Build: ``python -m build`` instead of ``uvx nox -s build``
    - Test: ``python -m pytest`` instead of ``uvx nox -s pytest``
    - Lint: ``python -m ruff/black/isort`` instead of ``uvx nox -s lint``
    - Docs: ``python -m sphinx`` instead of ``uvx nox -s docs``

Dependency Installation Problems
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptom**: Complex dependency installation fails

**Solution**:
- Simplify dependency installation steps
- Use ``python -m pip install`` consistently
- Remove dependencies on specific tools like ``uv``

Platform-Specific Issues
~~~~~~~~~~~~~~~~~~~~~~~~

**Symptom**: Build fails on specific platforms

**Solution**:
- Use platform-specific setup scripts
- Add conditional execution based on runner OS
- Ensure proper environment setup for each platform

Best Practices
---------------

1. **Always use caching** for dependencies and build artifacts
2. **Minimize build matrix** to focus on critical configurations
3. **Use conditional execution** to skip unnecessary steps
4. **Implement fast mode** for development testing
5. **Set up concurrency control** to avoid resource waste
6. **Use reusable jobs** for better code organization and maintenance
7. **Replace tool-specific commands** with standard Python module commands
8. **Handle platform differences** with conditional steps
