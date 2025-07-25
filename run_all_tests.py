#!/usr/bin/env python3
"""
Test runner script to execute all tests using pytest.

This script provides a single entry point to run the entire test suite
for the codebase agent project. It discovers and runs all tests located
in the 'test/' directory.
"""

import sys
import subprocess


def main():
    """Run all tests using pytest with uv."""
    print("=================================================")
    print("  Starting Codebase Agent Test Suite")
    print("=================================================")

    # Check if uv is available
    try:
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
        use_uv = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("UV not found, using standard python/pytest")
        use_uv = False

    # Run tests
    if use_uv:
        print("Running tests with uv...")
        try:
            result = subprocess.run([
                "uv", "run", "pytest", 
                "-v", "--durations=10", "test/"
            ])
            result_code = result.returncode
        except FileNotFoundError:
            print("UV command not found, falling back to standard pytest...")
            result_code = subprocess.run([
                sys.executable, "-m", "pytest", 
                "-v", "--durations=10", "test/"
            ]).returncode
    else:
        print("Running tests with standard python/pytest...")
        result_code = subprocess.run([
            sys.executable, "-m", "pytest", 
            "-v", "--durations=10", "test/"
        ]).returncode

    print("=================================================")
    print(f"  Test Suite Finished - Exit Code: {result_code}")
    print("=================================================")

    sys.exit(result_code)


if __name__ == "__main__":
    main()
