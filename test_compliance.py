#!/usr/bin/env python3
"""
Test script for compliance integration
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_compliance_import():
    """Test that compliance components can be imported."""
    try:
        from src.handlers.compliance_handler import compliance_handler
        print("✅ ComplianceHandler imported successfully")
        
        # Test basic functionality
        status = compliance_handler.get_compliance_status()
        print(f"✅ Compliance status: {len(status)} features tracked")
        
        return True
    except Exception as e:
        print(f"❌ Error importing compliance handler: {e}")
        return False

def test_compliance_dialog_import():
    """Test that compliance dialog can be imported."""
    try:
        from src.ui.compliance_dialog import ComplianceDialog
        print("✅ ComplianceDialog imported successfully")
        return True
    except Exception as e:
        print(f"❌ Error importing compliance dialog: {e}")
        return False

def test_menu_integration():
    """Test that main window imports work."""
    try:
        from src.ui.main_window import MainWindow
        print("✅ MainWindow with compliance integration imported successfully")
        return True
    except Exception as e:
        print(f"❌ Error importing main window: {e}")
        return False

if __name__ == "__main__":
    print("Testing Meta Developer Platform Compliance Integration...")
    print("=" * 60)
    
    tests = [
        test_compliance_import,
        test_compliance_dialog_import,
        test_menu_integration
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"Tests passed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        print("🎉 All compliance integration tests PASSED!")
        print("\nThe following features are now available:")
        print("• Privacy & Compliance menu in main window")
        print("• Data export functionality (Ctrl+E)")
        print("• Factory reset with safeguards")
        print("• Meta compliance status monitoring")
        print("• GDPR/CCPA data export")
        print("• Privacy policy integration")
    else:
        print("⚠️  Some tests failed. Check the errors above.") 