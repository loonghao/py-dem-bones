#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Run tests for py-dem-bones package using uvx nox.

This script provides a convenient way to run tests for the py-dem-bones package
using uvx nox. It can be used to run different test sessions, such as basic tests,
full test suite, or coverage tests.
"""

import os
import sys
import subprocess
import argparse


def main():
    """Run tests for py-dem-bones package."""
    parser = argparse.ArgumentParser(description="Run tests for py-dem-bones package")
    parser.add_argument(
        "--session",
        "-s",
        choices=["pytest", "basic-test", "coverage", "test-windows"],
        default="pytest",
        help="Nox session to run (default: pytest)",
    )
    parser.add_argument(
        "--skip-install",
        action="store_true",
        help="Skip installing the package (use pytest_skip_install session)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    args = parser.parse_args()

    # Determine the session to run
    session = args.session
    if args.skip_install and session == "pytest":
        session = "pytest_skip_install"

    # Build the command
    cmd = ["uvx", "nox", "-s", session]
    if args.verbose:
        cmd.append("-v")

    # Print the command
    print(f"Running: {' '.join(cmd)}")

    # Run the command
    try:
        subprocess.run(cmd, check=True)
        print(f"Successfully ran {session} session")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Error running {session} session: {e}")
        return e.returncode


if __name__ == "__main__":
    sys.exit(main())
