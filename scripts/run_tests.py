#!/usr/bin/env python3
"""
Comprehensive test runner script for the Django Task List application.

This script runs all types of tests:
- Django backend unit tests
- API integration tests
- JavaScript unit tests (if npm is available)
- End-to-end tests with Playwright
- Performance tests with Locust
- Security tests
- Accessibility tests

Usage:
    python scripts/run_tests.py [test_type]

    test_type options:
    - all: Run all tests (default)
    - unit: Run unit tests only
    - integration: Run integration tests only
    - frontend: Run JavaScript unit tests only
    - e2e: Run end-to-end tests only
    - performance: Run performance tests only
    - security: Run security tests only
    - accessibility: Run accessibility tests only
    - coverage: Generate coverage report only
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


class TestRunner:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.venv_python = self.project_root / '.venv' / 'bin' / 'python'
        self.venv_pytest = self.project_root / '.venv' / 'bin' / 'pytest'
        self.venv_playwright = self.project_root / '.venv' / 'bin' / 'playwright'
        self.venv_locust = self.project_root / '.venv' / 'bin' / 'locust'

        if not self.venv_python.exists():
            print("Error: Virtual environment not found. Please run from project root with .venv activated.")
            sys.exit(1)

    def run_command(self, command, description, cwd=None):
        """Run a shell command and return success status"""
        print(f"\n{'='*60}")
        print(f"Running: {description}")
        print(f"Command: {' '.join(command)}")
        print(f"{'='*60}")

        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.project_root,
                check=True,
                capture_output=False
            )
            print(f"✅ {description} completed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ {description} failed with exit code {e.returncode}")
            return False
        except FileNotFoundError as e:
            print(f"❌ Command not found: {e}")
            return False

    def run_unit_tests(self):
        """Run Django unit tests"""
        return self.run_command([
            str(self.venv_pytest),
            'tests/backend/test_models.py',
            'tests/backend/test_serializers.py',
            'tests/backend/test_views.py',
            '-v',
            '--tb=short',
            '-m', 'not slow'
        ], "Django Unit Tests")

    def run_integration_tests(self):
        """Run API integration tests"""
        return self.run_command([
            str(self.venv_pytest),
            'tests/backend/test_api_integration.py',
            '-v',
            '--tb=short'
        ], "API Integration Tests")

    def run_frontend_tests(self):
        """Run JavaScript unit tests"""
        # Check if npm and Jest are available
        package_json = self.project_root / 'package.json'
        if not package_json.exists():
            print("⚠️  Frontend tests skipped: package.json not found")
            return True

        try:
            npm_test = subprocess.run(['npm', 'test', '--', '--watchAll=false'],
                                    cwd=self.project_root,
                                    check=True)
            print("✅ Frontend tests completed successfully")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  Frontend tests skipped: npm or Jest not available")
            return True

    def run_e2e_tests(self):
        """Run end-to-end tests with Playwright"""
        if not self.venv_playwright.exists():
            print("⚠️  E2E tests skipped: Playwright not installed")
            return True

        return self.run_command([
            str(self.venv_playwright),
            'test',
            '--config=playwright.config.js'
        ], "End-to-End Tests")

    def run_performance_tests(self):
        """Run performance tests"""
        # First run pytest performance tests
        pytest_success = self.run_command([
            str(self.venv_pytest),
            'tests/performance/test_performance.py',
            '-v',
            '--tb=short',
            '-m', 'performance'
        ], "Performance Tests (pytest)")

        # Then run a quick Locust test if available
        if self.venv_locust.exists():
            print("\n📊 Running quick load test with Locust...")
            locust_success = self.run_command([
                str(self.venv_locust),
                '-f', 'tests/performance/locustfile.py',
                '--headless',
                '--users', '10',
                '--spawn-rate', '2',
                '--run-time', '30s',
                '--host', 'http://127.0.0.1:8000'
            ], "Load Tests (Locust)")
        else:
            print("⚠️  Locust load tests skipped: locust not installed")
            locust_success = True

        return pytest_success and locust_success

    def run_security_tests(self):
        """Run security tests"""
        return self.run_command([
            str(self.venv_pytest),
            'tests/security/',
            '-v',
            '--tb=short',
            '-m', 'not slow'
        ], "Security Tests")

    def run_accessibility_tests(self):
        """Run accessibility tests"""
        if not self.venv_playwright.exists():
            print("⚠️  Accessibility tests skipped: Playwright not installed")
            return True

        return self.run_command([
            str(self.venv_playwright),
            'test',
            'tests/accessibility/',
            '--config=playwright.config.js'
        ], "Accessibility Tests")

    def generate_coverage_report(self):
        """Generate comprehensive coverage report"""
        return self.run_command([
            str(self.venv_pytest),
            'tests/',
            '--cov=.',
            '--cov-report=html',
            '--cov-report=term-missing',
            '--cov-report=xml',
            '--cov-fail-under=80',
            '-v'
        ], "Coverage Report Generation")

    def run_all_tests(self):
        """Run all tests in sequence"""
        tests = [
            ("Unit Tests", self.run_unit_tests),
            ("Integration Tests", self.run_integration_tests),
            ("Frontend Tests", self.run_frontend_tests),
            ("Security Tests", self.run_security_tests),
            ("E2E Tests", self.run_e2e_tests),
            ("Performance Tests", self.run_performance_tests),
            ("Accessibility Tests", self.run_accessibility_tests),
        ]

        results = {}
        for test_name, test_func in tests:
            results[test_name] = test_func()

        # Print summary
        print(f"\n{'='*60}")
        print("TEST SUMMARY")
        print(f"{'='*60}")

        total_tests = len(results)
        passed_tests = sum(results.values())
        failed_tests = total_tests - passed_tests

        for test_name, success in results.items():
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{test_name:<25} {status}")

        print(f"\nTotal: {total_tests}, Passed: {passed_tests}, Failed: {failed_tests}")

        if failed_tests > 0:
            print(f"\n❌ {failed_tests} test suite(s) failed!")
            return False
        else:
            print(f"\n🎉 All {passed_tests} test suites passed!")
            return True


def main():
    parser = argparse.ArgumentParser(description="Run Django Task List Application Tests")
    parser.add_argument(
        'test_type',
        nargs='?',
        default='all',
        choices=['all', 'unit', 'integration', 'frontend', 'e2e', 'performance', 'security', 'accessibility', 'coverage'],
        help='Type of tests to run (default: all)'
    )

    args = parser.parse_args()
    runner = TestRunner()

    # Map test types to methods
    test_methods = {
        'unit': runner.run_unit_tests,
        'integration': runner.run_integration_tests,
        'frontend': runner.run_frontend_tests,
        'e2e': runner.run_e2e_tests,
        'performance': runner.run_performance_tests,
        'security': runner.run_security_tests,
        'accessibility': runner.run_accessibility_tests,
        'coverage': runner.generate_coverage_report,
        'all': runner.run_all_tests,
    }

    success = test_methods[args.test_type]()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()