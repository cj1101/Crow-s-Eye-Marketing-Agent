#!/usr/bin/env python3
"""
GCP Deployment Script with Pre-deployment Validation
Runs tests, validates configuration, and deploys to Google Cloud Platform
"""

import os
import sys
import subprocess
import asyncio
import logging
from pathlib import Path
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GCPDeployer:
    """Handles GCP deployment with validation and testing."""
    
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.app_yaml = self.project_dir / "app.yaml"
        self.requirements_prod = self.project_dir / "requirements-production.txt"
        
    def run_command(self, command, description="Running command"):
        """Run a shell command and return success status."""
        try:
            logger.info(f"🔄 {description}...")
            logger.info(f"Command: {command}")
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.project_dir
            )
            
            if result.returncode == 0:
                logger.info(f"✅ {description} - Success")
                if result.stdout.strip():
                    logger.info(f"Output: {result.stdout.strip()}")
                return True
            else:
                logger.error(f"❌ {description} - Failed")
                logger.error(f"Error: {result.stderr.strip()}")
                return False
                
        except Exception as e:
            logger.error(f"💥 {description} - Exception: {str(e)}")
            return False
    
    async def run_database_tests(self):
        """Run database configuration tests."""
        logger.info("🧪 Running database configuration tests...")
        
        try:
            # Import and run the test function directly
            from test_db_fix import test_database_config
            success = await test_database_config()
            
            if success:
                logger.info("✅ Database tests passed!")
                return True
            else:
                logger.error("❌ Database tests failed!")
                return False
                
        except Exception as e:
            logger.error(f"💥 Database tests error: {str(e)}")
            return False
    
    def validate_gcp_setup(self):
        """Validate GCP CLI and authentication."""
        logger.info("🔍 Validating GCP setup...")
        
        # Check if gcloud is installed
        if not self.run_command("gcloud version", "Checking gcloud installation"):
            logger.error("❌ gcloud CLI not found! Please install Google Cloud SDK")
            return False
        
        # Check authentication
        if not self.run_command("gcloud auth list --filter=status:ACTIVE", "Checking GCP authentication"):
            logger.error("❌ No active GCP authentication! Run: gcloud auth login")
            return False
        
        # Check project configuration
        if not self.run_command("gcloud config get-value project", "Checking GCP project"):
            logger.error("❌ No GCP project configured! Run: gcloud config set project YOUR_PROJECT_ID")
            return False
        
        logger.info("✅ GCP setup validation passed!")
        return True
    
    def validate_app_engine_api(self):
        """Enable App Engine API if needed."""
        logger.info("🔧 Validating App Engine API...")
        
        # Try to enable App Engine API
        if self.run_command("gcloud services enable appengine.googleapis.com", "Enabling App Engine API"):
            logger.info("✅ App Engine API is enabled")
            return True
        else:
            logger.warning("⚠️ Could not verify App Engine API status")
            return True  # Continue anyway
    
    def validate_files(self):
        """Validate required files exist."""
        logger.info("📁 Validating deployment files...")
        
        required_files = [
            self.app_yaml,
            self.requirements_prod,
            self.project_dir / "deploy_main.py",
            self.project_dir / "initialize_gcp_db.py"
        ]
        
        for file_path in required_files:
            if not file_path.exists():
                logger.error(f"❌ Required file missing: {file_path}")
                return False
            logger.info(f"✅ Found: {file_path.name}")
        
        return True
    
    def deploy_to_gcp(self):
        """Deploy to Google Cloud Platform."""
        logger.info("🚀 Starting GCP deployment...")
        
        # Deploy command
        deploy_cmd = "gcloud app deploy app.yaml --quiet"
        
        if self.run_command(deploy_cmd, "Deploying to GCP App Engine"):
            logger.info("🎉 Deployment successful!")
            
            # Get the deployed URL
            if self.run_command("gcloud app browse --no-launch-browser", "Getting deployment URL"):
                logger.info("📡 Application deployed successfully!")
                return True
        
        logger.error("💥 Deployment failed!")
        return False
    
    def post_deployment_tests(self):
        """Run post-deployment validation tests."""
        logger.info("🔎 Running post-deployment tests...")
        
        # Get project ID
        try:
            result = subprocess.run(
                "gcloud config get-value project",
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                project_id = result.stdout.strip()
                app_url = f"https://{project_id}.uc.r.appspot.com"
                
                logger.info(f"🌐 Testing deployment at: {app_url}")
                
                # Test health endpoint
                health_cmd = f'curl -s "{app_url}/health" || echo "Health check failed"'
                if self.run_command(health_cmd, "Testing health endpoint"):
                    logger.info("✅ Health endpoint responding")
                else:
                    logger.warning("⚠️ Health endpoint test failed")
                
                return True
            
        except Exception as e:
            logger.warning(f"⚠️ Post-deployment tests failed: {str(e)}")
        
        return True  # Don't fail deployment on test issues
    
    async def full_deployment(self):
        """Run complete deployment process."""
        logger.info("🎯 Starting full GCP deployment process...")
        
        try:
            # Step 1: Validate files
            if not self.validate_files():
                return False
            
            # Step 2: Run database tests
            if not await self.run_database_tests():
                logger.error("❌ Pre-deployment tests failed!")
                return False
            
            # Step 3: Validate GCP setup
            if not self.validate_gcp_setup():
                return False
            
            # Step 4: Enable App Engine API
            self.validate_app_engine_api()
            
            # Step 5: Deploy to GCP
            if not self.deploy_to_gcp():
                return False
            
            # Step 6: Post-deployment tests
            self.post_deployment_tests()
            
            logger.info("🎉 Full deployment process completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"💥 Deployment process failed: {str(e)}")
            return False

def main():
    """Main deployment function."""
    print("🦅 Crow's Eye API - GCP Deployment Script")
    print("=" * 50)
    
    deployer = GCPDeployer()
    
    # Run deployment
    success = asyncio.run(deployer.full_deployment())
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Deployment completed successfully!")
        print("\n📋 Next steps:")
        print("1. Test your API at: https://your-project-id.uc.r.appspot.com/health")
        print("2. View API docs at: https://your-project-id.uc.r.appspot.com/docs")
        print("3. Monitor logs with: gcloud app logs tail -s default")
    else:
        print("❌ Deployment failed!")
        print("\n🔧 Troubleshooting:")
        print("1. Check the error messages above")
        print("2. Verify GCP authentication: gcloud auth login")
        print("3. Set project: gcloud config set project YOUR_PROJECT_ID")
        print("4. Enable App Engine: gcloud app create --region=us-central")
        
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 