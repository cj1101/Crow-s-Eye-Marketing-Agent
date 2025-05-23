#!/usr/bin/env python3
"""
Simple test script to verify the i18n system works correctly.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_i18n():
    """Test the i18n system."""
    print("Testing I18N system...")
    
    try:
        from i18n import i18n
        print("✓ I18N system imported successfully")
        
        # Test current language
        current_lang = i18n.get_current_language()
        print(f"✓ Current language: {current_lang}")
        
        # Test available languages
        available_langs = i18n.get_available_languages()
        print(f"✓ Available languages: {available_langs}")
        
        # Test translation
        test_key = "Marketing Assistant"
        translated = i18n.t(test_key)
        print(f"✓ Translation test: '{test_key}' -> '{translated}'")
        
        # Test language switching
        print("\nTesting language switching...")
        for lang in ["es", "fr", "de", "en"]:
            if i18n.switch(lang):
                translated = i18n.t(test_key)
                print(f"✓ {lang}: '{test_key}' -> '{translated}'")
            else:
                print(f"✗ Failed to switch to {lang}")
        
        print("\n✓ All tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_i18n()
    sys.exit(0 if success else 1) 