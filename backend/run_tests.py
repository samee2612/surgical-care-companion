#!/usr/bin/env python3
"""
Test Runner for TKA Voice Agent
Runs all tests including call scheduling and API endpoint tests
"""

import subprocess
import sys
import os
import argparse

def run_tests(test_type="all", verbose=False):
    """Run TKA Voice Agent tests"""
    print("🧪 Running TKA Voice Agent Tests...")
    print("=" * 60)
    
    # Change to backend directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Determine which tests to run
    test_files = []
    if test_type == "all":
        test_files = [
            "tests/test_call_scheduling.py",
            "tests/test_api_endpoints.py"
        ]
        print("📋 Running ALL tests (Call Scheduling + API Endpoints)")
    elif test_type == "scheduling":
        test_files = ["tests/test_call_scheduling.py"]
        print("📅 Running Call Scheduling tests only")
    elif test_type == "api":
        test_files = ["tests/test_api_endpoints.py"]
        print("🌐 Running API Endpoint tests only")
    else:
        print(f"❌ Unknown test type: {test_type}")
        return 1
    
    print("=" * 60)
    
    # Build pytest command
    cmd = [sys.executable, "-m", "pytest"] + test_files
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-v")  # Always use verbose for better output
    
    cmd.extend(["--tb=short", "--no-header"])
    
    # Run tests
    result = subprocess.run(cmd, capture_output=False)
    
    print("=" * 60)
    if result.returncode == 0:
        print("✅ All tests passed!")
        print("\n📊 Test Summary:")
        if "scheduling" in test_type or test_type == "all":
            print("   🔸 Call Scheduling: 11 tests covering scheduling logic")
        if "api" in test_type or test_type == "all":
            print("   🔸 API Endpoints: Comprehensive endpoint testing")
    else:
        print("❌ Some tests failed!")
        print("🔍 Check the output above for details")
        
    return result.returncode

def main():
    parser = argparse.ArgumentParser(description="Run TKA Voice Agent tests")
    parser.add_argument(
        "--type", 
        choices=["all", "scheduling", "api"], 
        default="all",
        help="Type of tests to run (default: all)"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Check prerequisites
    print("🔍 Checking prerequisites...")
    
    # Check if PostgreSQL is running
    postgres_check = subprocess.run(
        ["docker", "ps", "--filter", "name=tka_postgres", "--format", "{{.Names}}"],
        capture_output=True, text=True
    )
    
    if "tka_postgres" not in postgres_check.stdout:
        print("⚠️  Warning: PostgreSQL container 'tka_postgres' is not running")
        print("   Run: docker-compose up -d postgres")
        print("   Continuing anyway (tests may fail)...")
    else:
        print("✅ PostgreSQL container is running")
    
    print()
    
    return run_tests(args.type, args.verbose)

if __name__ == "__main__":
    sys.exit(main()) 