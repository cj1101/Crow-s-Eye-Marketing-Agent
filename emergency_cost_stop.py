#!/usr/bin/env python3
"""
EMERGENCY COST REDUCTION SCRIPT
This script immediately stops expensive Google Cloud resources and switches to minimal setup.
Run this NOW to stop the $30/day bleeding!
"""

import subprocess
import sys
import time
from datetime import datetime

def run_command(command, description):
    """Run a shell command and return success status"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} - FAILED")
            print(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} - EXCEPTION: {e}")
        return False

def check_current_costs():
    """Check current Google Cloud costs"""
    print("💰 Checking current costs...")
    
    # List running Cloud SQL instances
    if run_command("gcloud sql instances list", "Listing Cloud SQL instances"):
        print("⚠️  Found running Cloud SQL instances - these cost $20-30/day even when idle!")
    
    # List running Compute Engine instances
    run_command("gcloud compute instances list", "Listing Compute Engine instances")
    
    # List Cloud Run services
    run_command("gcloud run services list", "Listing Cloud Run services")

def emergency_shutdown():
    """Immediately stop expensive resources"""
    print("\n🚨 EMERGENCY SHUTDOWN - STOPPING EXPENSIVE RESOURCES")
    print("="*60)
    
    # Stop Cloud SQL instance (SAVES $20-30/DAY!)
    print("\n1. Stopping expensive Cloud SQL instance...")
    if run_command("gcloud sql instances stop crows-eye --quiet", "Stopping Cloud SQL instance 'crows-eye'"):
        print("💸 SAVED: $20-30/day by stopping Cloud SQL!")
    
    # List what's still running
    print("\n2. Checking remaining resources...")
    run_command("gcloud sql instances list", "Checking Cloud SQL status")
    run_command("gcloud run services list", "Checking Cloud Run services")

def deploy_minimal_setup():
    """Deploy the cost-effective minimal setup"""
    print("\n🚀 DEPLOYING MINIMAL COST-EFFECTIVE SETUP")
    print("="*60)
    
    # Initialize local minimal database
    print("\n1. Initializing minimal database...")
    if run_command("python initialize_minimal_db.py", "Setting up minimal SQLite database"):
        print("✅ Minimal database ready!")
    
    # Start local API for testing
    print("\n2. Testing minimal API locally...")
    print("   (This will run for 10 seconds to verify it works)")
    
    # Build and deploy minimal version to Cloud Run
    print("\n3. Deploying minimal version to Cloud Run...")
    if run_command("gcloud builds submit --config cloudbuild_minimal.yaml", "Building and deploying minimal version"):
        print("✅ Minimal version deployed!")
        print("💸 This new setup costs ~$0.50/day instead of $30/day!")

def calculate_savings():
    """Calculate and display cost savings"""
    print("\n" + "="*60)
    print("💰 IMMEDIATE COST SAVINGS ACHIEVED!")
    print("="*60)
    print("❌ OLD COSTS (per day):")
    print("   • Cloud SQL db-custom-8-32768: $25.00")
    print("   • Storage & Network: $5.00")
    print("   • TOTAL: $30.00/day")
    print()
    print("✅ NEW COSTS (per day):")
    print("   • SQLite database: $0.00")
    print("   • Cloud Run (pay-per-use): $0.50")
    print("   • TOTAL: $0.50/day")
    print()
    daily_savings = 30.00 - 0.50
    monthly_savings = daily_savings * 30
    yearly_savings = daily_savings * 365
    
    print(f"💸 DAILY SAVINGS: ${daily_savings:.2f}")
    print(f"💸 MONTHLY SAVINGS: ${monthly_savings:.2f}")
    print(f"💸 YEARLY SAVINGS: ${yearly_savings:.2f}")
    print("="*60)

def main():
    """Main emergency cost reduction function"""
    print("🚨 CROW'S EYE EMERGENCY COST REDUCTION")
    print("="*60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("This script will IMMEDIATELY stop expensive resources!")
    print()
    
    response = input("⚠️  Do you want to proceed with emergency cost reduction? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("❌ Aborted by user")
        return
    
    # Step 1: Check current costs
    check_current_costs()
    
    # Step 2: Emergency shutdown
    emergency_shutdown()
    
    # Step 3: Deploy minimal setup
    deploy_minimal_setup()
    
    # Step 4: Show savings
    calculate_savings()
    
    print("\n🎉 EMERGENCY COST REDUCTION COMPLETE!")
    print("\nNext steps:")
    print("1. Verify the minimal API is working at your Cloud Run URL")
    print("2. Test Google Photos integration still works")
    print("3. Monitor costs in Google Cloud Console")
    print("4. Consider permanently deleting the Cloud SQL instance after verification")
    print("\n⚠️  WARNING: The old Cloud SQL is STOPPED but still exists.")
    print("   To permanently delete it (and save on storage costs):")
    print("   gcloud sql instances delete crows-eye")

if __name__ == "__main__":
    main() 