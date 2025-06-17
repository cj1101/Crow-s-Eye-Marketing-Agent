#!/usr/bin/env python3
"""
Comprehensive security scanning script for Crow's Eye API.
This script validates security configurations and identifies potential vulnerabilities.
"""

import asyncio
import subprocess
import json
import os
import sys
import tempfile
from typing import Dict, List, Any
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class SecurityScanner:
    """Comprehensive security scanner for the API."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.results = {
            "overall_score": 0,
            "scans": {},
            "recommendations": [],
            "critical_issues": [],
            "warnings": []
        }
    
    def run_all_scans(self) -> Dict[str, Any]:
        """Run all security scans."""
        logger.info("Starting comprehensive security scan...")
        
        # Code security scans
        self.scan_code_security()
        self.scan_dependencies()
        self.scan_secrets()
        
        # Configuration scans
        self.scan_configuration()
        self.scan_deployment_config()
        
        # Runtime security scans
        asyncio.run(self.scan_runtime_security())
        
        # Calculate overall score
        self.calculate_security_score()
        
        # Generate report
        self.generate_report()
        
        return self.results
    
    def scan_code_security(self):
        """Scan code for security vulnerabilities using Bandit."""
        logger.info("Scanning code security with Bandit...")
        
        try:
            cmd = [
                "bandit",
                "-r", str(self.project_root / "crow_eye_api"),
                "-f", "json",
                "-o", "/tmp/bandit_results.json",
                "-ll"  # Only show low severity and above
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if os.path.exists("/tmp/bandit_results.json"):
                with open("/tmp/bandit_results.json", "r") as f:
                    bandit_results = json.load(f)
                
                self.results["scans"]["bandit"] = {
                    "status": "completed",
                    "issues_found": len(bandit_results.get("results", [])),
                    "high_severity": len([r for r in bandit_results.get("results", []) if r.get("issue_severity") == "HIGH"]),
                    "medium_severity": len([r for r in bandit_results.get("results", []) if r.get("issue_severity") == "MEDIUM"]),
                    "low_severity": len([r for r in bandit_results.get("results", []) if r.get("issue_severity") == "LOW"])
                }
                
                # Add critical issues
                for issue in bandit_results.get("results", []):
                    if issue.get("issue_severity") == "HIGH":
                        self.results["critical_issues"].append({
                            "type": "code_security",
                            "severity": "HIGH",
                            "message": issue.get("issue_text", ""),
                            "file": issue.get("filename", ""),
                            "line": issue.get("line_number", 0)
                        })
            
        except Exception as e:
            logger.error(f"Bandit scan failed: {e}")
            self.results["scans"]["bandit"] = {"status": "failed", "error": str(e)}
    
    def scan_dependencies(self):
        """Scan dependencies for known vulnerabilities using Safety."""
        logger.info("Scanning dependencies with Safety...")
        
        try:
            cmd = ["safety", "check", "--json", "--output", "/tmp/safety_results.json"]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            
            if os.path.exists("/tmp/safety_results.json"):
                with open("/tmp/safety_results.json", "r") as f:
                    safety_results = json.load(f)
                
                self.results["scans"]["safety"] = {
                    "status": "completed",
                    "vulnerabilities_found": len(safety_results),
                    "details": safety_results
                }
                
                # Add critical dependency issues
                for vuln in safety_results:
                    self.results["critical_issues"].append({
                        "type": "dependency_vulnerability",
                        "severity": "HIGH",
                        "message": f"Vulnerable package: {vuln.get('package', 'unknown')} - {vuln.get('advisory', '')}",
                        "package": vuln.get("package", ""),
                        "installed_version": vuln.get("installed_version", ""),
                        "vulnerable_spec": vuln.get("vulnerable_spec", "")
                    })
            
        except Exception as e:
            logger.error(f"Safety scan failed: {e}")
            self.results["scans"]["safety"] = {"status": "failed", "error": str(e)}
    
    def scan_secrets(self):
        """Scan for hardcoded secrets and sensitive information."""
        logger.info("Scanning for hardcoded secrets...")
        
        secret_patterns = [
            r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{8,}['\"]",
            r"(?i)(secret|token|key)\s*[:=]\s*['\"][^'\"]{16,}['\"]",
            r"(?i)(api_key|apikey)\s*[:=]\s*['\"][^'\"]{16,}['\"]",
            r"(?i)(database_url|db_url)\s*[:=]\s*['\"][^'\"]+['\"]",
            r"(?i)(jwt_secret|jwt_key)\s*[:=]\s*['\"][^'\"]+['\"]",
            r"(?i)(private_key|privkey)\s*[:=]\s*['\"][^'\"]+['\"]",
            r"(?i)(access_token|auth_token)\s*[:=]\s*['\"][^'\"]+['\"]"
        ]
        
        secrets_found = []
        
        for pattern in secret_patterns:
            try:
                cmd = ["grep", "-r", "-n", "-E", pattern, str(self.project_root)]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.stdout:
                    for line in result.stdout.split('\n'):
                        if line.strip() and not any(exclude in line.lower() for exclude in ['test', 'example', 'placeholder', 'your-']):
                            secrets_found.append(line.strip())
            
            except Exception as e:
                logger.error(f"Secret scan failed for pattern {pattern}: {e}")
        
        self.results["scans"]["secrets"] = {
            "status": "completed",
            "secrets_found": len(secrets_found),
            "details": secrets_found[:10]  # Limit output
        }
        
        # Add warnings for potential secrets
        for secret in secrets_found[:5]:  # Limit warnings
            self.results["warnings"].append({
                "type": "potential_secret",
                "message": f"Potential hardcoded secret detected: {secret[:100]}..."
            })
    
    def scan_configuration(self):
        """Scan configuration files for security issues."""
        logger.info("Scanning configuration security...")
        
        config_issues = []
        
        # Check app.yaml
        app_yaml_path = self.project_root / "app.yaml"
        if app_yaml_path.exists():
            with open(app_yaml_path, "r") as f:
                content = f.read()
                
                # Check for security configurations
                if "JWT_SECRET_KEY" in content and "change-this" in content.lower():
                    config_issues.append("Default JWT secret key detected in app.yaml")
                
                if "automatic_scaling" not in content:
                    config_issues.append("Automatic scaling not configured")
                
                if "readiness_check" not in content:
                    config_issues.append("Health checks not properly configured")
        
        # Check requirements.txt for security
        requirements_path = self.project_root / "requirements.txt"
        if requirements_path.exists():
            with open(requirements_path, "r") as f:
                content = f.read()
                
                if "bandit" not in content:
                    config_issues.append("Security scanning tool (bandit) not in requirements")
                
                if "pytest" not in content:
                    config_issues.append("Testing framework not in requirements")
        
        self.results["scans"]["configuration"] = {
            "status": "completed",
            "issues_found": len(config_issues),
            "details": config_issues
        }
        
        # Add critical configuration issues
        for issue in config_issues:
            if "secret" in issue.lower() or "default" in issue.lower():
                self.results["critical_issues"].append({
                    "type": "configuration",
                    "severity": "HIGH",
                    "message": issue
                })
    
    def scan_deployment_config(self):
        """Scan deployment configuration for security best practices."""
        logger.info("Scanning deployment configuration...")
        
        deployment_issues = []
        
        # Check Dockerfile if exists
        dockerfile_path = self.project_root / "Dockerfile"
        if dockerfile_path.exists():
            with open(dockerfile_path, "r") as f:
                content = f.read()
                
                if "USER root" in content or "USER 0" in content:
                    deployment_issues.append("Docker container running as root")
                
                if "COPY . ." in content:
                    deployment_issues.append("Docker copying entire context (security risk)")
        
        # Check for HTTPS enforcement
        main_py_path = self.project_root / "crow_eye_api" / "main.py"
        if main_py_path.exists():
            with open(main_py_path, "r") as f:
                content = f.read()
                
                if "Strict-Transport-Security" not in content:
                    deployment_issues.append("HTTPS enforcement (HSTS) not configured")
                
                if "allow_origins=[\"*\"]" in content:
                    deployment_issues.append("CORS configured to allow all origins")
        
        self.results["scans"]["deployment"] = {
            "status": "completed",
            "issues_found": len(deployment_issues),
            "details": deployment_issues
        }
    
    async def scan_runtime_security(self):
        """Scan runtime security if API is running."""
        logger.info("Scanning runtime security...")
        
        try:
            import httpx
            
            # Test local API if running
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get("http://localhost:8000/health", timeout=5)
                    
                    security_headers = [
                        "X-Content-Type-Options",
                        "X-Frame-Options",
                        "X-XSS-Protection",
                        "Strict-Transport-Security",
                        "Content-Security-Policy"
                    ]
                    
                    missing_headers = []
                    for header in security_headers:
                        if header not in response.headers:
                            missing_headers.append(header)
                    
                    self.results["scans"]["runtime"] = {
                        "status": "completed",
                        "api_accessible": True,
                        "security_headers_missing": missing_headers,
                        "response_time": response.elapsed.total_seconds()
                    }
                    
                except Exception:
                    self.results["scans"]["runtime"] = {
                        "status": "skipped",
                        "reason": "API not accessible for runtime testing"
                    }
        
        except ImportError:
            self.results["scans"]["runtime"] = {
                "status": "skipped",
                "reason": "httpx not available for runtime testing"
            }
    
    def calculate_security_score(self):
        """Calculate overall security score."""
        score = 100
        
        # Deduct points for critical issues
        score -= len(self.results["critical_issues"]) * 15
        
        # Deduct points for warnings
        score -= len(self.results["warnings"]) * 5
        
        # Deduct points for failed scans
        failed_scans = sum(1 for scan in self.results["scans"].values() if scan.get("status") == "failed")
        score -= failed_scans * 10
        
        # Bonus points for security features
        if any("security" in str(scan).lower() for scan in self.results["scans"].values()):
            score += 5
        
        self.results["overall_score"] = max(0, min(100, score))
    
    def generate_report(self):
        """Generate security report with recommendations."""
        logger.info("Generating security recommendations...")
        
        recommendations = []
        
        # General recommendations
        recommendations.extend([
            "Implement regular security scans in CI/CD pipeline",
            "Use environment variables for all sensitive configuration",
            "Enable comprehensive logging and monitoring",
            "Implement rate limiting on all endpoints",
            "Use HTTPS in production with proper SSL/TLS configuration",
            "Regularly update dependencies to patch vulnerabilities",
            "Implement proper backup and disaster recovery procedures",
            "Use strong authentication and authorization mechanisms",
            "Implement input validation and sanitization",
            "Configure proper CORS policies"
        ])
        
        # Specific recommendations based on findings
        if self.results["scans"].get("bandit", {}).get("issues_found", 0) > 0:
            recommendations.append("Fix code security issues identified by Bandit")
        
        if self.results["scans"].get("safety", {}).get("vulnerabilities_found", 0) > 0:
            recommendations.append("Update vulnerable dependencies identified by Safety")
        
        if self.results["scans"].get("secrets", {}).get("secrets_found", 0) > 0:
            recommendations.append("Remove hardcoded secrets and use secure secret management")
        
        self.results["recommendations"] = recommendations
    
    def print_report(self):
        """Print formatted security report."""
        print("\n" + "="*60)
        print("CROW'S EYE API SECURITY SCAN REPORT")
        print("="*60)
        
        print(f"\nOVERALL SECURITY SCORE: {self.results['overall_score']}/100")
        
        if self.results["overall_score"] >= 80:
            print("✅ EXCELLENT - API security posture is strong")
        elif self.results["overall_score"] >= 60:
            print("⚠️  GOOD - Some security improvements needed")
        elif self.results["overall_score"] >= 40:
            print("🟡 FAIR - Multiple security issues require attention")
        else:
            print("🔴 POOR - Critical security issues must be addressed")
        
        print("\nSCAN RESULTS:")
        for scan_name, scan_result in self.results["scans"].items():
            status = scan_result.get("status", "unknown")
            print(f"  {scan_name.upper()}: {status}")
            
            if scan_name == "bandit" and scan_result.get("issues_found", 0) > 0:
                print(f"    - Issues: {scan_result['issues_found']}")
                print(f"    - High: {scan_result.get('high_severity', 0)}")
                print(f"    - Medium: {scan_result.get('medium_severity', 0)}")
                print(f"    - Low: {scan_result.get('low_severity', 0)}")
            
            elif scan_name == "safety" and scan_result.get("vulnerabilities_found", 0) > 0:
                print(f"    - Vulnerabilities: {scan_result['vulnerabilities_found']}")
            
            elif scan_name == "secrets" and scan_result.get("secrets_found", 0) > 0:
                print(f"    - Potential secrets: {scan_result['secrets_found']}")
        
        if self.results["critical_issues"]:
            print(f"\n🔴 CRITICAL ISSUES ({len(self.results['critical_issues'])}):")
            for issue in self.results["critical_issues"][:5]:  # Show first 5
                print(f"  - {issue['message']}")
        
        if self.results["warnings"]:
            print(f"\n⚠️  WARNINGS ({len(self.results['warnings'])}):")
            for warning in self.results["warnings"][:5]:  # Show first 5
                print(f"  - {warning['message']}")
        
        print(f"\n💡 TOP RECOMMENDATIONS:")
        for i, rec in enumerate(self.results["recommendations"][:5], 1):
            print(f"  {i}. {rec}")
        
        print("\n" + "="*60)


def main():
    """Main function to run security scan."""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = os.getcwd()
    
    scanner = SecurityScanner(project_root)
    results = scanner.run_all_scans()
    scanner.print_report()
    
    # Save detailed results to file
    with open("security_scan_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to: security_scan_results.json")
    
    # Exit with error code if critical issues found
    if results["critical_issues"] or results["overall_score"] < 50:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main() 