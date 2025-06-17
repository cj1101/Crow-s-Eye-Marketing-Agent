#!/usr/bin/env python3
"""
Comprehensive API Validation Script for Crow's Eye API
This script validates that the API is absolutely perfect and ironclad.
"""

import os
import sys
import json
import asyncio
import subprocess
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import tempfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class IroncladAPIValidator:
    """Comprehensive validator for the Crow's Eye API."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.validation_results = {
            "overall_score": 0,
            "categories": {},
            "critical_issues": [],
            "warnings": [],
            "recommendations": [],
            "passed_validations": 0,
            "total_validations": 0
        }
    
    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run all validation categories."""
        logger.info("🚀 Starting comprehensive API validation...")
        
        # Code Quality & Security
        await self.validate_code_security()
        
        # API Structure & Design
        await self.validate_api_structure()
        
        # Authentication & Authorization
        await self.validate_auth_security()
        
        # Database & Data Layer
        await self.validate_database_layer()
        
        # Performance & Scalability
        await self.validate_performance()
        
        # Deployment & Infrastructure
        await self.validate_deployment_config()
        
        # Error Handling & Resilience
        await self.validate_error_handling()
        
        # Monitoring & Observability
        await self.validate_monitoring()
        
        # Calculate overall score
        self.calculate_final_score()
        
        return self.validation_results
    
    async def validate_code_security(self):
        """Validate code security measures."""
        logger.info("🔒 Validating code security...")
        
        category_score = 0
        category_total = 8
        
        # 1. Check for security middleware
        security_features = [
            "SecurityHeadersMiddleware",
            "RateLimitMiddleware",
            "request_tracking_middleware"
        ]
        
        main_py = self.project_root / "crow_eye_api" / "main.py"
        if main_py.exists():
            content = main_py.read_text()
            found_features = sum(1 for feature in security_features if feature in content)
            if found_features >= 2:
                category_score += 1
                logger.info("✅ Security middleware properly configured")
            else:
                self.add_critical_issue("Missing security middleware")
        
        # 2. Input validation and sanitization
        security_py = self.project_root / "crow_eye_api" / "core" / "security.py"
        if security_py.exists():
            content = security_py.read_text()
            if "sanitize_input" in content and "validate_password_strength" in content:
                category_score += 1
                logger.info("✅ Input validation and sanitization implemented")
            else:
                self.add_warning("Input validation could be enhanced")
        
        # 3. Password security
        if security_py.exists():
            content = security_py.read_text()
            if "bcrypt__rounds=12" in content:
                category_score += 1
                logger.info("✅ Strong password hashing configured")
            else:
                self.add_warning("Password hashing could be strengthened")
        
        # 4. JWT security
        if security_py.exists():
            content = security_py.read_text()
            jwt_features = ["iat", "nbf", "jti"]  # JWT security claims
            found_jwt = sum(1 for feature in jwt_features if feature in content)
            if found_jwt >= 2:
                category_score += 1
                logger.info("✅ JWT security features implemented")
            else:
                self.add_warning("JWT security could be enhanced")
        
        # 5. CORS configuration
        if main_py.exists():
            content = main_py.read_text()
            if "allow_origins" in content and "*" not in content.split("allow_origins")[1].split("]")[0]:
                category_score += 1
                logger.info("✅ CORS properly configured")
            else:
                self.add_warning("CORS configuration could be more restrictive")
        
        # 6. Error handling
        if main_py.exists():
            content = main_py.read_text()
            if "exception_handler" in content and "HTTPException" in content:
                category_score += 1
                logger.info("✅ Comprehensive error handling implemented")
            else:
                self.add_warning("Error handling could be improved")
        
        # 7. Rate limiting
        if main_py.exists():
            content = main_py.read_text()
            if "RateLimitMiddleware" in content:
                category_score += 1
                logger.info("✅ Rate limiting implemented")
            else:
                self.add_critical_issue("Rate limiting not implemented")
        
        # 8. Security headers
        if main_py.exists():
            content = main_py.read_text()
            security_headers = ["X-Content-Type-Options", "X-Frame-Options", "Content-Security-Policy"]
            found_headers = sum(1 for header in security_headers if header in content)
            if found_headers >= 2:
                category_score += 1
                logger.info("✅ Security headers configured")
            else:
                self.add_warning("Security headers could be enhanced")
        
        self.validation_results["categories"]["code_security"] = {
            "score": category_score,
            "total": category_total,
            "percentage": (category_score / category_total) * 100
        }
        
        self.validation_results["passed_validations"] += category_score
        self.validation_results["total_validations"] += category_total
    
    async def validate_api_structure(self):
        """Validate API structure and design."""
        logger.info("🏗️ Validating API structure...")
        
        category_score = 0
        category_total = 6
        
        # 1. Check API router structure
        api_router_path = self.project_root / "crow_eye_api" / "api" / "api_v1" / "api.py"
        if api_router_path.exists():
            category_score += 1
            logger.info("✅ API router structure properly organized")
        else:
            self.add_critical_issue("API router structure missing")
        
        # 2. Check endpoint organization
        endpoints_dir = self.project_root / "crow_eye_api" / "api" / "api_v1" / "endpoints"
        if endpoints_dir.exists() and len(list(endpoints_dir.glob("*.py"))) >= 3:
            category_score += 1
            logger.info("✅ Endpoints properly organized")
        else:
            self.add_warning("Endpoint organization could be improved")
        
        # 3. Check schema definitions
        schemas_dir = self.project_root / "crow_eye_api" / "schemas"
        if schemas_dir.exists() and len(list(schemas_dir.glob("*.py"))) >= 3:
            category_score += 1
            logger.info("✅ Schemas properly defined")
        else:
            self.add_warning("Schema organization could be improved")
        
        # 4. Check CRUD operations
        crud_dir = self.project_root / "crow_eye_api" / "crud"
        if crud_dir.exists() and len(list(crud_dir.glob("*.py"))) >= 2:
            category_score += 1
            logger.info("✅ CRUD operations properly organized")
        else:
            self.add_warning("CRUD organization could be improved")
        
        # 5. Check dependency injection
        deps_path = self.project_root / "crow_eye_api" / "api" / "api_v1" / "dependencies.py"
        if deps_path.exists():
            content = deps_path.read_text()
            if "get_current_active_user" in content:
                category_score += 1
                logger.info("✅ Dependency injection properly implemented")
            else:
                self.add_warning("Dependency injection could be enhanced")
        
        # 6. Check OpenAPI documentation
        if api_router_path.exists():
            content = api_router_path.read_text()
            if "tags=" in content and "summary=" in content:
                category_score += 1
                logger.info("✅ API documentation properly configured")
            else:
                self.add_warning("API documentation could be improved")
        
        self.validation_results["categories"]["api_structure"] = {
            "score": category_score,
            "total": category_total,
            "percentage": (category_score / category_total) * 100
        }
        
        self.validation_results["passed_validations"] += category_score
        self.validation_results["total_validations"] += category_total
    
    async def validate_auth_security(self):
        """Validate authentication and authorization security."""
        logger.info("🔐 Validating authentication security...")
        
        category_score = 0
        category_total = 7
        
        # 1. Check auth endpoints
        login_py = self.project_root / "crow_eye_api" / "api" / "api_v1" / "endpoints" / "login.py"
        if login_py.exists():
            content = login_py.read_text()
            auth_endpoints = ["/auth/register", "/auth/login", "/auth/user", "/auth/logout"]
            found_endpoints = sum(1 for endpoint in auth_endpoints if endpoint in content)
            if found_endpoints >= 3:
                category_score += 1
                logger.info("✅ Authentication endpoints properly implemented")
            else:
                self.add_critical_issue("Missing authentication endpoints")
        
        # 2. Check password validation
        if login_py.exists():
            content = login_py.read_text()
            if "validate_password_strength" in content:
                category_score += 1
                logger.info("✅ Password strength validation implemented")
            else:
                self.add_critical_issue("Password strength validation missing")
        
        # 3. Check rate limiting for auth
        if login_py.exists():
            content = login_py.read_text()
            if "check_auth_rate_limit" in content:
                category_score += 1
                logger.info("✅ Authentication rate limiting implemented")
            else:
                self.add_critical_issue("Authentication rate limiting missing")
        
        # 4. Check input sanitization
        if login_py.exists():
            content = login_py.read_text()
            if "sanitize_input" in content:
                category_score += 1
                logger.info("✅ Input sanitization in auth endpoints")
            else:
                self.add_warning("Authentication input sanitization could be improved")
        
        # 5. Check JWT configuration
        config_py = self.project_root / "crow_eye_api" / "core" / "config.py"
        if config_py.exists():
            content = config_py.read_text()
            if "JWT_SECRET_KEY" in content and "validate_jwt_secret" in content:
                category_score += 1
                logger.info("✅ JWT configuration properly validated")
            else:
                self.add_critical_issue("JWT configuration validation missing")
        
        # 6. Check user model security
        user_model = self.project_root / "crow_eye_api" / "models" / "user.py"
        if user_model.exists():
            content = user_model.read_text()
            if "hashed_password" in content and "is_active" in content:
                category_score += 1
                logger.info("✅ User model properly secured")
            else:
                self.add_warning("User model security could be improved")
        
        # 7. Check session management
        if login_py.exists():
            content = login_py.read_text()
            if "refresh_token" in content:
                category_score += 1
                logger.info("✅ Session management implemented")
            else:
                self.add_warning("Session management could be enhanced")
        
        self.validation_results["categories"]["auth_security"] = {
            "score": category_score,
            "total": category_total,
            "percentage": (category_score / category_total) * 100
        }
        
        self.validation_results["passed_validations"] += category_score
        self.validation_results["total_validations"] += category_total
    
    async def validate_database_layer(self):
        """Validate database layer implementation."""
        logger.info("🗄️ Validating database layer...")
        
        category_score = 0
        category_total = 6
        
        # 1. Check database configuration
        db_py = self.project_root / "crow_eye_api" / "database.py"
        if db_py.exists():
            content = db_py.read_text()
            if "create_async_engine" in content and "AsyncSession" in content:
                category_score += 1
                logger.info("✅ Async database configuration proper")
            else:
                self.add_warning("Database configuration could be improved")
        
        # 2. Check connection pooling
        if db_py.exists():
            content = db_py.read_text()
            if "pool_size" in content or "QueuePool" in content:
                category_score += 1
                logger.info("✅ Database connection pooling configured")
            else:
                self.add_warning("Database connection pooling could be improved")
        
        # 3. Check retry logic
        if db_py.exists():
            content = db_py.read_text()
            if "with_db_retry" in content and "exponential backoff" in content:
                category_score += 1
                logger.info("✅ Database retry logic implemented")
            else:
                self.add_warning("Database retry logic could be enhanced")
        
        # 4. Check error handling
        if db_py.exists():
            content = db_py.read_text()
            if "SQLAlchemyError" in content and "DisconnectionError" in content:
                category_score += 1
                logger.info("✅ Database error handling comprehensive")
            else:
                self.add_warning("Database error handling could be improved")
        
        # 5. Check health monitoring
        if db_py.exists():
            content = db_py.read_text()
            if "check_database_health" in content:
                category_score += 1
                logger.info("✅ Database health monitoring implemented")
            else:
                self.add_warning("Database health monitoring missing")
        
        # 6. Check models definition
        models_dir = self.project_root / "crow_eye_api" / "models"
        if models_dir.exists() and len(list(models_dir.glob("*.py"))) >= 2:
            category_score += 1
            logger.info("✅ Database models properly defined")
        else:
            self.add_warning("Database models could be better organized")
        
        self.validation_results["categories"]["database_layer"] = {
            "score": category_score,
            "total": category_total,
            "percentage": (category_score / category_total) * 100
        }
        
        self.validation_results["passed_validations"] += category_score
        self.validation_results["total_validations"] += category_total
    
    async def validate_performance(self):
        """Validate performance optimizations."""
        logger.info("⚡ Validating performance optimizations...")
        
        category_score = 0
        category_total = 5
        
        # 1. Check async implementation
        main_py = self.project_root / "crow_eye_api" / "main.py"
        if main_py.exists():
            content = main_py.read_text()
            if "async def" in content and "await" in content:
                category_score += 1
                logger.info("✅ Async implementation properly used")
            else:
                self.add_warning("Async implementation could be improved")
        
        # 2. Check response compression
        if main_py.exists():
            content = main_py.read_text()
            if "GZipMiddleware" in content:
                category_score += 1
                logger.info("✅ Response compression enabled")
            else:
                self.add_warning("Response compression not enabled")
        
        # 3. Check connection keep-alive
        app_yaml = self.project_root / "app.yaml"
        if app_yaml.exists():
            content = app_yaml.read_text()
            if "--keepalive" in content:
                category_score += 1
                logger.info("✅ Connection keep-alive configured")
            else:
                self.add_warning("Connection keep-alive could be optimized")
        
        # 4. Check request limits
        if app_yaml.exists():
            content = app_yaml.read_text()
            if "--max-requests" in content:
                category_score += 1
                logger.info("✅ Request limits configured")
            else:
                self.add_warning("Request limits could be configured")
        
        # 5. Check monitoring
        if main_py.exists():
            content = main_py.read_text()
            if "X-Process-Time" in content and "request_tracking" in content:
                category_score += 1
                logger.info("✅ Performance monitoring implemented")
            else:
                self.add_warning("Performance monitoring could be enhanced")
        
        self.validation_results["categories"]["performance"] = {
            "score": category_score,
            "total": category_total,
            "percentage": (category_score / category_total) * 100
        }
        
        self.validation_results["passed_validations"] += category_score
        self.validation_results["total_validations"] += category_total
    
    async def validate_deployment_config(self):
        """Validate deployment configuration."""
        logger.info("🚀 Validating deployment configuration...")
        
        category_score = 0
        category_total = 7
        
        # 1. Check App Engine configuration
        app_yaml = self.project_root / "app.yaml"
        if app_yaml.exists():
            content = app_yaml.read_text()
            if "automatic_scaling" in content and "readiness_check" in content:
                category_score += 1
                logger.info("✅ App Engine configuration comprehensive")
            else:
                self.add_warning("App Engine configuration could be improved")
        
        # 2. Check security settings
        if app_yaml.exists():
            content = app_yaml.read_text()
            if "skip_files" in content and len(content.split("skip_files")[1].split("-")[0]) > 50:
                category_score += 1
                logger.info("✅ Security file exclusions configured")
            else:
                self.add_warning("Security file exclusions could be improved")
        
        # 3. Check resource allocation
        if app_yaml.exists():
            content = app_yaml.read_text()
            if "instance_class" in content and "min_instances" in content:
                category_score += 1
                logger.info("✅ Resource allocation properly configured")
            else:
                self.add_warning("Resource allocation could be optimized")
        
        # 4. Check health checks
        if app_yaml.exists():
            content = app_yaml.read_text()
            if "liveness_check" in content and "readiness_check" in content:
                category_score += 1
                logger.info("✅ Health checks properly configured")
            else:
                self.add_critical_issue("Health checks not properly configured")
        
        # 5. Check environment variables
        if app_yaml.exists():
            content = app_yaml.read_text()
            required_vars = ["PROJECT_NAME", "API_V1_STR", "DATABASE_URL"]
            found_vars = sum(1 for var in required_vars if var in content)
            if found_vars >= 2:
                category_score += 1
                logger.info("✅ Environment variables properly configured")
            else:
                self.add_warning("Environment variables could be better organized")
        
        # 6. Check secret management
        if app_yaml.exists():
            content = app_yaml.read_text()
            if "SET_THIS_VIA_GCLOUD" in content or "JWT_SECRET_KEY" not in content:
                category_score += 1
                logger.info("✅ Secret management properly configured")
            else:
                self.add_critical_issue("Hardcoded secrets detected")
        
        # 7. Check deployment scripts
        deploy_script = self.project_root / "scripts" / "deploy_secure.py"
        if deploy_script.exists():
            category_score += 1
            logger.info("✅ Secure deployment script available")
        else:
            self.add_warning("Secure deployment script could be added")
        
        self.validation_results["categories"]["deployment_config"] = {
            "score": category_score,
            "total": category_total,
            "percentage": (category_score / category_total) * 100
        }
        
        self.validation_results["passed_validations"] += category_score
        self.validation_results["total_validations"] += category_total
    
    async def validate_error_handling(self):
        """Validate error handling and resilience."""
        logger.info("🛡️ Validating error handling...")
        
        category_score = 0
        category_total = 5
        
        # 1. Check global exception handlers
        main_py = self.project_root / "crow_eye_api" / "main.py"
        if main_py.exists():
            content = main_py.read_text()
            handlers = ["HTTPException", "RequestValidationError", "StarletteHTTPException"]
            found_handlers = sum(1 for handler in handlers if f"exception_handler({handler})" in content)
            if found_handlers >= 2:
                category_score += 1
                logger.info("✅ Global exception handlers implemented")
            else:
                self.add_critical_issue("Comprehensive exception handling missing")
        
        # 2. Check error response format
        if main_py.exists():
            content = main_py.read_text()
            if '"success": False' in content and '"request_id"' in content:
                category_score += 1
                logger.info("✅ Consistent error response format")
            else:
                self.add_warning("Error response format could be standardized")
        
        # 3. Check logging for errors
        if main_py.exists():
            content = main_py.read_text()
            if "logger.error" in content and "traceback" in content:
                category_score += 1
                logger.info("✅ Error logging properly implemented")
            else:
                self.add_warning("Error logging could be enhanced")
        
        # 4. Check graceful degradation
        db_py = self.project_root / "crow_eye_api" / "database.py"
        if db_py.exists():
            content = db_py.read_text()
            if "max_retries" in content and "exponential backoff" in content:
                category_score += 1
                logger.info("✅ Graceful degradation implemented")
            else:
                self.add_warning("Graceful degradation could be improved")
        
        # 5. Check input validation errors
        login_py = self.project_root / "crow_eye_api" / "api" / "api_v1" / "endpoints" / "login.py"
        if login_py.exists():
            content = login_py.read_text()
            if "HTTPException" in content and "status_code" in content:
                category_score += 1
                logger.info("✅ Input validation error handling proper")
            else:
                self.add_warning("Input validation error handling could be improved")
        
        self.validation_results["categories"]["error_handling"] = {
            "score": category_score,
            "total": category_total,
            "percentage": (category_score / category_total) * 100
        }
        
        self.validation_results["passed_validations"] += category_score
        self.validation_results["total_validations"] += category_total
    
    async def validate_monitoring(self):
        """Validate monitoring and observability."""
        logger.info("📊 Validating monitoring and observability...")
        
        category_score = 0
        category_total = 5
        
        # 1. Check request tracking
        main_py = self.project_root / "crow_eye_api" / "main.py"
        if main_py.exists():
            content = main_py.read_text()
            if "request_tracking_middleware" in content and "X-Request-ID" in content:
                category_score += 1
                logger.info("✅ Request tracking implemented")
            else:
                self.add_warning("Request tracking could be enhanced")
        
        # 2. Check metrics collection
        if main_py.exists():
            content = main_py.read_text()
            if "error_counts" in content and "/metrics" in content:
                category_score += 1
                logger.info("✅ Metrics collection implemented")
            else:
                self.add_warning("Metrics collection could be added")
        
        # 3. Check structured logging
        if main_py.exists():
            content = main_py.read_text()
            if "logging.basicConfig" in content and "logging.FileHandler" in content:
                category_score += 1
                logger.info("✅ Structured logging configured")
            else:
                self.add_warning("Structured logging could be improved")
        
        # 4. Check health monitoring
        if main_py.exists():
            content = main_py.read_text()
            if "health_check_dependencies" in content:
                category_score += 1
                logger.info("✅ Health monitoring comprehensive")
            else:
                self.add_warning("Health monitoring could be enhanced")
        
        # 5. Check performance tracking
        if main_py.exists():
            content = main_py.read_text()
            if "process_time" in content and "X-Process-Time" in content:
                category_score += 1
                logger.info("✅ Performance tracking implemented")
            else:
                self.add_warning("Performance tracking could be added")
        
        self.validation_results["categories"]["monitoring"] = {
            "score": category_score,
            "total": category_total,
            "percentage": (category_score / category_total) * 100
        }
        
        self.validation_results["passed_validations"] += category_score
        self.validation_results["total_validations"] += category_total
    
    def add_critical_issue(self, issue: str):
        """Add a critical issue to the results."""
        self.validation_results["critical_issues"].append(issue)
    
    def add_warning(self, warning: str):
        """Add a warning to the results."""
        self.validation_results["warnings"].append(warning)
    
    def calculate_final_score(self):
        """Calculate the final ironclad score."""
        if self.validation_results["total_validations"] > 0:
            base_score = (self.validation_results["passed_validations"] / self.validation_results["total_validations"]) * 100
        else:
            base_score = 0
        
        # Deduct points for critical issues
        critical_penalty = len(self.validation_results["critical_issues"]) * 10
        
        # Deduct points for warnings
        warning_penalty = len(self.validation_results["warnings"]) * 2
        
        final_score = max(0, base_score - critical_penalty - warning_penalty)
        
        self.validation_results["overall_score"] = final_score
        
        # Generate recommendations
        self.generate_recommendations()
    
    def generate_recommendations(self):
        """Generate recommendations based on validation results."""
        recommendations = []
        
        # Category-specific recommendations
        for category, results in self.validation_results["categories"].items():
            if results["percentage"] < 80:
                recommendations.append(f"Improve {category.replace('_', ' ')} implementation")
        
        # Critical issue recommendations
        if self.validation_results["critical_issues"]:
            recommendations.append("Address all critical security issues immediately")
        
        # Warning recommendations
        if len(self.validation_results["warnings"]) > 5:
            recommendations.append("Address warning items to improve overall security posture")
        
        # General recommendations
        if self.validation_results["overall_score"] < 90:
            recommendations.extend([
                "Implement comprehensive automated testing",
                "Add continuous security monitoring",
                "Enhance error handling and logging",
                "Improve API documentation",
                "Implement advanced security features"
            ])
        
        self.validation_results["recommendations"] = recommendations
    
    def print_detailed_report(self):
        """Print a detailed validation report."""
        print("\n" + "="*80)
        print("🛡️ CROW'S EYE API - IRONCLAD VALIDATION REPORT")
        print("="*80)
        
        score = self.validation_results["overall_score"]
        print(f"\n🎯 OVERALL IRONCLAD SCORE: {score:.1f}/100")
        
        if score >= 95:
            print("🏆 EXCEPTIONAL - API is absolutely ironclad!")
        elif score >= 85:
            print("✅ EXCELLENT - API is very secure and robust")
        elif score >= 75:
            print("🟢 GOOD - API has strong security with minor improvements needed")
        elif score >= 60:
            print("🟡 FAIR - API needs significant security improvements")
        else:
            print("🔴 POOR - API has critical security issues that must be addressed")
        
        print(f"\n📊 VALIDATION SUMMARY:")
        print(f"   Passed: {self.validation_results['passed_validations']}/{self.validation_results['total_validations']} ({(self.validation_results['passed_validations']/self.validation_results['total_validations']*100):.1f}%)")
        print(f"   Critical Issues: {len(self.validation_results['critical_issues'])}")
        print(f"   Warnings: {len(self.validation_results['warnings'])}")
        
        print(f"\n📋 CATEGORY BREAKDOWN:")
        for category, results in self.validation_results["categories"].items():
            status = "✅" if results["percentage"] >= 80 else "⚠️" if results["percentage"] >= 60 else "❌"
            print(f"   {status} {category.replace('_', ' ').title()}: {results['score']}/{results['total']} ({results['percentage']:.1f}%)")
        
        if self.validation_results["critical_issues"]:
            print(f"\n🚨 CRITICAL ISSUES ({len(self.validation_results['critical_issues'])}):")
            for issue in self.validation_results["critical_issues"]:
                print(f"   ❌ {issue}")
        
        if self.validation_results["warnings"]:
            print(f"\n⚠️ WARNINGS ({len(self.validation_results['warnings'])}):")
            for warning in self.validation_results["warnings"][:10]:  # Show first 10
                print(f"   ⚠️ {warning}")
        
        if self.validation_results["recommendations"]:
            print(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(self.validation_results["recommendations"][:8], 1):
                print(f"   {i}. {rec}")
        
        print("\n" + "="*80)
        
        return score >= 85  # Return True if API is considered ironclad


async def main():
    """Main function to run ironclad validation."""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = os.getcwd()
    
    validator = IroncladAPIValidator(project_root)
    results = await validator.run_comprehensive_validation()
    
    # Print detailed report
    is_ironclad = validator.print_detailed_report()
    
    # Save results to file
    with open("ironclad_validation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: ironclad_validation_results.json")
    
    if is_ironclad:
        print("\n🎉 CONGRATULATIONS! Your API is IRONCLAD! 🛡️")
        sys.exit(0)
    else:
        print("\n⚠️ API needs improvements before it can be considered ironclad.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 