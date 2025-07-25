#!/usr/bin/env python3
"""
Test runner script to execute all tests using pytest.

This script provides a single entry point to run the entire test suite
for the codebase agent project. It discovers and runs all tests located
in the 'test/' directory.
"""

import sys
import pytest


def main():
    """Run all tests using pytest."""
    print("=================================================")
    print("  Starting Codebase Agent Test Suite")
    print("=================================================")

    # Run pytest on the 'test' directory with verbose output
    # and report test durations for the 10 slowest tests.
    result_code = pytest.main(["-v", "--durations=10", "test/"])

    print("=================================================")
    print(f"  Test Suite Finished - Exit Code: {result_code}")
    print("=================================================")

    sys.exit(result_code)


if __name__ == "__main__":
    main()
