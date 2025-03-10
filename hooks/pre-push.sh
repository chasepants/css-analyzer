#!/bin/bash

# Run tests and generate coverage report
coverage run -m pytest
test_result=$?

# Check if tests failed (non-zero exit code)
if [ $test_result -ne 0 ]; then
    echo "Error: Tests failed with exit code $test_result."
    echo "Please fix failing tests before pushing."
    exit 1
fi

# Check coverage percentage (only if tests pass)
coverage_percentage=$(coverage report | awk 'NR==3 {print $4}' | tr -d '%')

# Define minimum acceptable coverage
min_coverage=95

# Compare coverage and exit if below minimum
if (( $(echo "$coverage_percentage < $min_coverage" | bc -l) )); then
    echo "Error: Code coverage is below $min_coverage% ($coverage_percentage%)."
    echo "Please improve test coverage before pushing."
    exit 1
else
    echo "Tests passed and code coverage check passed ($coverage_percentage%)."
    exit 0
fi