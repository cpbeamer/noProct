"""Security test runner with comprehensive reporting"""
import unittest
import sys
import os
import time
import json
from pathlib import Path
from datetime import datetime
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class SecurityTestRunner:
    """Run all security tests and generate report"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'tests_skipped': 0,
            'security_issues': [],
            'recommendations': [],
            'test_details': {}
        }
    
    def run_all_tests(self):
        """Run all security test suites"""
        print("=" * 60)
        print("SECURITY TEST SUITE FOR NOPROCT.IO")
        print("=" * 60)
        print(f"Starting security tests at {datetime.now()}\n")
        
        test_modules = [
            ('test_core', 'Core Security Tests'),
            ('test_security_comprehensive', 'Comprehensive Security Tests'),
            ('test_service_security', 'Service Security Tests'),
            ('test_filesystem_security', 'Filesystem Security Tests'),
            ('test_integration_security', 'Integration Security Tests'),
        ]
        
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        for module_name, description in test_modules:
            print(f"\nLoading {description}...")
            try:
                module = loader.loadTestsFromName(module_name)
                suite.addTests(module)
                print(f"  ✓ Loaded {module.countTestCases()} tests")
            except Exception as e:
                print(f"  ✗ Failed to load: {e}")
                self.results['security_issues'].append({
                    'type': 'TEST_LOAD_FAILURE',
                    'module': module_name,
                    'error': str(e)
                })
        
        print(f"\n{'=' * 60}")
        print(f"Running {suite.countTestCases()} security tests...")
        print(f"{'=' * 60}\n")
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        self.analyze_results(result)
        self.generate_recommendations()
        self.save_report()
        
        return result.wasSuccessful()
    
    def analyze_results(self, result):
        """Analyze test results for security issues"""
        self.results['tests_run'] = result.testsRun
        self.results['tests_passed'] = result.testsRun - len(result.failures) - len(result.errors)
        self.results['tests_failed'] = len(result.failures) + len(result.errors)
        self.results['tests_skipped'] = len(result.skipped)
        
        for test, traceback in result.failures:
            self.analyze_failure(test, traceback, 'FAILURE')
        
        for test, traceback in result.errors:
            self.analyze_failure(test, traceback, 'ERROR')
        
        for test, reason in result.skipped:
            self.results['test_details'][str(test)] = {
                'status': 'SKIPPED',
                'reason': reason
            }
    
    def analyze_failure(self, test, trace, failure_type):
        """Analyze individual test failure for security implications"""
        test_name = str(test)
        
        self.results['test_details'][test_name] = {
            'status': failure_type,
            'traceback': trace
        }
        
        security_keywords = [
            ('privilege', 'PRIVILEGE_ESCALATION'),
            ('permission', 'PERMISSION_ISSUE'),
            ('injection', 'INJECTION_VULNERABILITY'),
            ('traversal', 'PATH_TRAVERSAL'),
            ('encryption', 'ENCRYPTION_ISSUE'),
            ('authentication', 'AUTH_ISSUE'),
            ('rate_limit', 'RATE_LIMITING_ISSUE'),
            ('memory', 'MEMORY_SECURITY'),
            ('credential', 'CREDENTIAL_EXPOSURE'),
        ]
        
        trace_lower = trace.lower()
        for keyword, issue_type in security_keywords:
            if keyword in trace_lower or keyword in test_name.lower():
                self.results['security_issues'].append({
                    'type': issue_type,
                    'test': test_name,
                    'severity': self.assess_severity(issue_type),
                    'details': trace[:500]
                })
                break
    
    def assess_severity(self, issue_type):
        """Assess severity of security issue"""
        high_severity = [
            'PRIVILEGE_ESCALATION',
            'INJECTION_VULNERABILITY',
            'PATH_TRAVERSAL',
            'CREDENTIAL_EXPOSURE',
            'AUTH_ISSUE'
        ]
        
        medium_severity = [
            'PERMISSION_ISSUE',
            'ENCRYPTION_ISSUE',
            'RATE_LIMITING_ISSUE'
        ]
        
        if issue_type in high_severity:
            return 'HIGH'
        elif issue_type in medium_severity:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def generate_recommendations(self):
        """Generate security recommendations based on test results"""
        recommendations = []
        
        issue_types = set(issue['type'] for issue in self.results['security_issues'])
        
        recommendation_map = {
            'PRIVILEGE_ESCALATION': [
                'Implement proper privilege separation',
                'Use principle of least privilege',
                'Add UAC manifests for Windows',
                'Drop privileges after initialization'
            ],
            'PERMISSION_ISSUE': [
                'Set restrictive file permissions (600/640)',
                'Verify directory permissions',
                'Use ACLs for fine-grained control'
            ],
            'INJECTION_VULNERABILITY': [
                'Implement input validation and sanitization',
                'Use parameterized queries',
                'Escape special characters',
                'Use allowlists instead of denylists'
            ],
            'PATH_TRAVERSAL': [
                'Validate and sanitize file paths',
                'Use path.resolve() to normalize paths',
                'Implement chroot/jail for file operations',
                'Block directory traversal sequences'
            ],
            'ENCRYPTION_ISSUE': [
                'Use strong encryption algorithms (AES-256)',
                'Implement proper key management',
                'Use secure random number generation',
                'Enable TLS/SSL for network communication'
            ],
            'AUTH_ISSUE': [
                'Implement multi-factor authentication',
                'Use secure session management',
                'Implement account lockout policies',
                'Use strong password policies'
            ],
            'RATE_LIMITING_ISSUE': [
                'Implement rate limiting for all APIs',
                'Use exponential backoff',
                'Implement CAPTCHA for repeated failures',
                'Monitor for abuse patterns'
            ],
            'CREDENTIAL_EXPOSURE': [
                'Never log sensitive information',
                'Use secure credential storage (keyring)',
                'Implement credential rotation',
                'Mask credentials in UI and logs'
            ]
        }
        
        for issue_type in issue_types:
            if issue_type in recommendation_map:
                recommendations.extend(recommendation_map[issue_type])
        
        self.results['recommendations'] = list(set(recommendations))
    
    def save_report(self):
        """Save security test report"""
        report_dir = Path("test_reports")
        report_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"security_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\nSecurity report saved to: {report_file}")
        
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("SECURITY TEST SUMMARY")
        print("=" * 60)
        
        print(f"\nTests Run: {self.results['tests_run']}")
        print(f"Tests Passed: {self.results['tests_passed']}")
        print(f"Tests Failed: {self.results['tests_failed']}")
        print(f"Tests Skipped: {self.results['tests_skipped']}")
        
        if self.results['security_issues']:
            print(f"\n⚠️  Security Issues Found: {len(self.results['security_issues'])}")
            
            by_severity = {}
            for issue in self.results['security_issues']:
                severity = issue.get('severity', 'UNKNOWN')
                by_severity.setdefault(severity, []).append(issue)
            
            for severity in ['HIGH', 'MEDIUM', 'LOW']:
                if severity in by_severity:
                    print(f"  {severity}: {len(by_severity[severity])}")
                    for issue in by_severity[severity][:3]:
                        print(f"    - {issue['type']}: {issue['test'][:50]}")
        else:
            print("\n✅ No security issues detected!")
        
        if self.results['recommendations']:
            print(f"\n📋 Recommendations ({len(self.results['recommendations'])})")
            for rec in self.results['recommendations'][:5]:
                print(f"  • {rec}")
        
        success_rate = (self.results['tests_passed'] / self.results['tests_run'] * 100) if self.results['tests_run'] > 0 else 0
        
        print(f"\n{'=' * 60}")
        print(f"Overall Security Score: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("Status: ✅ EXCELLENT - Security measures are robust")
        elif success_rate >= 70:
            print("Status: ⚠️  GOOD - Some security improvements needed")
        elif success_rate >= 50:
            print("Status: ⚠️  FAIR - Significant security improvements required")
        else:
            print("Status: ❌ CRITICAL - Major security vulnerabilities present")
        
        print("=" * 60)


def main():
    """Main entry point"""
    runner = SecurityTestRunner()
    
    try:
        success = runner.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n\nFatal error during testing: {e}")
        traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    main()