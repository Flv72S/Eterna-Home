#!/usr/bin/env python3
"""
Implementation Status Test Runner
Executes all implementation tests and generates a comprehensive status report.
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import subprocess
import traceback

class ImplementationTestRunner:
    def __init__(self):
        self.results = []
        self.start_time = time.time()
        
    def run_test(self, test_name: str, test_file: str, test_function: str = None) -> Dict[str, Any]:
        """Run a single test and return results"""
        result = {
            "test": test_name,
            "file": test_file,
            "status": "❌ Failed",
            "error": None,
            "duration": 0,
            "notes": ""
        }
        
        try:
            start_time = time.time()
            
            # Run the test using pytest
            cmd = [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short", "-q"]
            if test_function:
                cmd.append(f"::{test_function}")
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )
            
            duration = time.time() - start_time
            result["duration"] = round(duration, 2)
            
            if process.returncode == 0:
                result["status"] = "✅ Passed"
                result["notes"] = f"Completed in {duration:.2f}s"
            else:
                result["status"] = "❌ Failed"
                result["error"] = process.stderr[:500] if process.stderr else "Unknown error"
                result["notes"] = f"Exit code: {process.returncode}"
                
        except subprocess.TimeoutExpired:
            result["status"] = "⏰ Timeout"
            result["error"] = "Test exceeded 60 second timeout"
            result["notes"] = "Test took too long to complete"
        except Exception as e:
            result["status"] = "💥 Error"
            result["error"] = str(e)
            result["notes"] = "Exception during test execution"
            
        return result
    
    def check_file_exists(self, file_path: str) -> Dict[str, Any]:
        """Check if a file exists and has content"""
        result = {
            "test": f"File exists: {file_path}",
            "file": file_path,
            "status": "❌ Missing",
            "error": None,
            "duration": 0,
            "notes": ""
        }
        
        try:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                if file_size > 0:
                    result["status"] = "✅ Present"
                    result["notes"] = f"Size: {file_size} bytes"
                else:
                    result["status"] = "⚠️ Empty"
                    result["notes"] = "File exists but is empty"
            else:
                result["status"] = "❌ Missing"
                result["notes"] = "File does not exist"
                
        except Exception as e:
            result["status"] = "💥 Error"
            result["error"] = str(e)
            
        return result
    
    def check_endpoint(self, endpoint: str, expected_status: int = 200) -> Dict[str, Any]:
        """Check if an API endpoint is accessible"""
        result = {
            "test": f"API endpoint: {endpoint}",
            "file": endpoint,
            "status": "❌ Failed",
            "error": None,
            "duration": 0,
            "notes": ""
        }
        
        try:
            import requests
            start_time = time.time()
            
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=10)
            duration = time.time() - start_time
            result["duration"] = round(duration, 2)
            
            if response.status_code == expected_status:
                result["status"] = "✅ Accessible"
                result["notes"] = f"Status: {response.status_code}, Time: {duration:.2f}s"
            else:
                result["status"] = "⚠️ Unexpected Status"
                result["notes"] = f"Expected {expected_status}, got {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            result["status"] = "🔌 Connection Error"
            result["notes"] = "Server not running or endpoint not available"
        except Exception as e:
            result["status"] = "💥 Error"
            result["error"] = str(e)
            
        return result
    
    def run_all_tests(self):
        """Run all implementation tests"""
        
        # Multi-tenant & Security Tests
        self.results.append(self.run_test(
            "Multi-tenant Isolation", 
            "tests/test_multitenant_isolation.py"
        ))
        
        self.results.append(self.run_test(
            "RBAC/PBAC Decorators", 
            "tests/test_rbac_pbac.py"
        ))
        
        self.results.append(self.run_test(
            "Structured Logging", 
            "tests/test_logging_structlog.py"
        ))
        
        self.results.append(self.run_test(
            "User Tenant Roles", 
            "tests/test_user_tenant_roles.py"
        ))
        
        # Multi-House Tests
        self.results.append(self.run_test(
            "User-House Relationships", 
            "tests/test_userhouse.py"
        ))
        
        # Document & BIM Tests
        self.results.append(self.run_test(
            "Document Upload", 
            "tests/test_document_upload.py"
        ))
        
        # Voice & AI Tests
        self.results.append(self.run_test(
            "Voice Commands", 
            "tests/test_voice_commands.py"
        ))
        
        # MFA & Auth Tests
        self.results.append(self.run_test(
            "MFA Enable/Disable", 
            "tests/test_mfa_enable_disable.py"
        ))
        
        # System & Validation Tests
        self.results.append(self.run_test(
            "System Router", 
            "tests/test_system_router.py"
        ))
        
        self.results.append(self.run_test(
            "File Validation", 
            "tests/test_file_validation.py"
        ))
        
        self.results.append(self.run_test(
            "Rate Limiting", 
            "tests/test_rate_limiting.py"
        ))
        
        # Security Reports
        self.results.append(self.check_file_exists("docs/security/owasp_report.html"))
        self.results.append(self.check_file_exists("docs/security/nikto_report.html"))
        self.results.append(self.check_file_exists("docs/security/bandit_report.json"))
        
        # API Endpoints (if server is running)
        self.results.append(self.check_endpoint("/health"))
        self.results.append(self.check_endpoint("/ready"))
        self.results.append(self.check_endpoint("/metrics"))
        
    def generate_report(self) -> str:
        """Generate markdown report"""
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if "✅" in r["status"])
        failed_tests = sum(1 for r in self.results if "❌" in r["status"])
        other_tests = total_tests - passed_tests - failed_tests
        
        total_duration = time.time() - self.start_time
        
        report = f"""# 🔍 IMPLEMENTATION STATUS REPORT - Eterna Home

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Total Duration:** {total_duration:.2f} seconds  
**Total Tests:** {total_tests}  
**Passed:** {passed_tests} ✅  
**Failed:** {failed_tests} ❌  
**Other:** {other_tests} ⚠️  

---

## 📊 Test Results

| Test | Description | Status | Duration | Notes |
|------|-------------|--------|----------|-------|
"""
        
        for result in self.results:
            status = result["status"]
            test_name = result["test"]
            duration = f"{result['duration']}s" if result["duration"] > 0 else "-"
            notes = result["notes"] or "-"
            
            report += f"| {test_name} | Implementation verification | {status} | {duration} | {notes} |\n"
        
        report += f"""
---

## 📈 Summary

- **Implementation Coverage:** {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)
- **Critical Issues:** {failed_tests}
- **Warnings:** {other_tests}

## 🔧 Recommendations

"""
        
        if failed_tests > 0:
            report += "- ⚠️ Address failed tests before production deployment\n"
        if other_tests > 0:
            report += "- 🔍 Review warnings and ensure proper implementation\n"
        if passed_tests == total_tests:
            report += "- ✅ All tests passed! Implementation is complete\n"
        
        report += f"""
## 📝 Detailed Results

"""
        
        for result in self.results:
            if result["error"]:
                report += f"### {result['test']}\n"
                report += f"**Status:** {result['status']}\n"
                report += f"**Error:** {result['error']}\n\n"
        
        return report
    
    def save_report(self, report: str):
        """Save report to files"""
        
        # Create docs/testing directory if it doesn't exist
        os.makedirs("docs/testing", exist_ok=True)
        
        # Save markdown report
        with open("docs/testing/IMPLEMENTATION_STATUS_REPORT.md", "w", encoding="utf-8") as f:
            f.write(report)
        
        # Save JSON report
        report_data = {
            "generated": datetime.now().isoformat(),
            "total_tests": len(self.results),
            "passed": sum(1 for r in self.results if "✅" in r["status"]),
            "failed": sum(1 for r in self.results if "❌" in r["status"]),
            "results": self.results
        }
        
        with open("docs/testing/IMPLEMENTATION_STATUS_REPORT.json", "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Reports saved to docs/testing/")

def main():
    """Main execution function"""
    print("🚀 Starting Implementation Status Test Runner...")
    
    runner = ImplementationTestRunner()
    
    try:
        runner.run_all_tests()
        report = runner.generate_report()
        runner.save_report(report)
        
        print("\n" + "="*60)
        print(report)
        print("="*60)
        
        print(f"\n✅ Implementation status report generated successfully!")
        print(f"📁 Reports saved to: docs/testing/IMPLEMENTATION_STATUS_REPORT.md")
        print(f"📊 JSON data saved to: docs/testing/IMPLEMENTATION_STATUS_REPORT.json")
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 