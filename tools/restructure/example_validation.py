#!/usr/bin/env python3
"""
Example script demonstrating how to use the ValidationSuite.

This script shows how to:
1. Run individual validation checks
2. Run the complete validation suite
3. Handle validation results
"""

from pathlib import Path
from validator import ValidationSuite


def main():
    """Run example validation checks."""
    # Initialize the validation suite
    repo_root = Path(__file__).parent.parent.parent
    validator = ValidationSuite(repo_root)
    
    print("=" * 80)
    print("VALIDATION SUITE EXAMPLE")
    print("=" * 80)
    print()
    
    # Example 1: Run a single validation check
    print("Example 1: Running Python syntax validation...")
    print("-" * 80)
    result = validator.validate_python_syntax()
    print(f"Success: {result.success}")
    print(f"Message: {result.message}")
    if result.errors:
        print(f"Errors: {len(result.errors)}")
        for error in result.errors[:3]:
            print(f"  - {error}")
    print()
    
    # Example 2: Run Django check
    print("Example 2: Running Django system check...")
    print("-" * 80)
    result = validator.validate_django()
    print(f"Success: {result.success}")
    print(f"Message: {result.message}")
    if result.errors:
        print(f"Errors: {len(result.errors)}")
        for error in result.errors[:3]:
            print(f"  - {error}")
    if result.warnings:
        print(f"Warnings: {len(result.warnings)}")
        for warning in result.warnings[:3]:
            print(f"  - {warning}")
    print()
    
    # Example 3: Run test discovery
    print("Example 3: Running test discovery...")
    print("-" * 80)
    result = validator.validate_test_discovery()
    print(f"Success: {result.success}")
    print(f"Message: {result.message}")
    print()
    
    # Example 4: Run complete validation suite
    print("Example 4: Running complete validation suite...")
    print("-" * 80)
    print("This will run all validation checks. This may take a few minutes...")
    print()
    
    # Uncomment the following lines to run the full suite
    # report = validator.run_all()
    # validator.print_report(report)
    
    print("To run the full validation suite, uncomment the lines in this script")
    print("or run: python validator.py --check all")
    print()
    
    print("=" * 80)
    print("EXAMPLE COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    main()
