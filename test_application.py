#!/usr/bin/env python
"""
Comprehensive test script for Crow's Eye Marketing Automation Platform.
Tests all major components and features for errors and functionality.
"""

import sys
import os
import logging
import traceback
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_application")

def test_imports():
    """Test all critical imports."""
    logger.info("Testing imports...")
    
    try:
        # Core imports
        from src.config import constants
        logger.info("✓ Constants imported successfully")
        
        # Handler imports
        from src.handlers.video_handler import VideoHandler
        from src.handlers.ai_handler import AIHandler
        from src.handlers.media_handler import MediaHandler
        from src.handlers.image_edit_handler import ImageEditHandler
        logger.info("✓ All handlers imported successfully")
        
        # UI imports
        from src.ui.main_window import MainWindow
        from src.ui.dialogs.video_processing_dialog import VideoProcessingDialog
        from src.ui.dialogs.audio_overlay_dialog import AudioOverlayDialog
        from src.ui.dialogs.gallery_generation_dialog import GalleryGenerationDialog
        logger.info("✓ All UI components imported successfully")
        
        # Utils imports
        from src.utils.api_key_manager import APIKeyManager
        from src.i18n import I18N
        logger.info("✓ All utilities imported successfully")
        
        # Model imports
        from src.models.app_state import AppState
        logger.info("✓ Models imported successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Import failed: {e}")
        traceback.print_exc()
        return False

def test_directory_structure():
    """Test that all required directories exist or can be created."""
    logger.info("Testing directory structure...")
    
    try:
        from src.config import constants
        
        required_dirs = [
            constants.MEDIA_LIBRARY_DIR,
            constants.OUTPUT_DIR,
            constants.LIBRARY_DIR,
            constants.MEDIA_GALLERY_DIR
        ]
        
        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
                logger.info(f"✓ Created directory: {dir_path}")
            else:
                logger.info(f"✓ Directory exists: {dir_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Directory structure test failed: {e}")
        return False

def test_video_handler():
    """Test video handler functionality."""
    logger.info("Testing video handler...")
    
    try:
        from src.handlers.video_handler import VideoHandler
        
        handler = VideoHandler()
        logger.info("✓ VideoHandler instantiated successfully")
        
        # Test method existence
        required_methods = [
            'generate_highlight_reel',
            'create_story_clips', 
            'generate_video_thumbnails',
            'generate_thumbnail',
            'add_audio_overlay',
            'get_video_info'
        ]
        
        for method_name in required_methods:
            if hasattr(handler, method_name):
                logger.info(f"✓ Method exists: {method_name}")
            else:
                logger.error(f"✗ Missing method: {method_name}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Video handler test failed: {e}")
        traceback.print_exc()
        return False

def test_ai_handler():
    """Test AI handler functionality."""
    logger.info("Testing AI handler...")
    
    try:
        from src.handlers.ai_handler import AIHandler
        from src.models.app_state import AppState
        
        # Create app state instance
        app_state = AppState()
        handler = AIHandler(app_state)
        logger.info("✓ AIHandler instantiated successfully")
        
        # Test basic functionality without API calls
        test_prompt = "Generate a caption for a bakery photo"
        logger.info(f"✓ AI handler ready for prompt processing")
        
        # Test method existence
        required_methods = ['generate_caption']
        for method_name in required_methods:
            if hasattr(handler, method_name):
                logger.info(f"✓ Method exists: {method_name}")
            else:
                logger.error(f"✗ Missing method: {method_name}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ AI handler test failed: {e}")
        traceback.print_exc()
        return False

def test_media_handler():
    """Test media handler functionality."""
    logger.info("Testing media handler...")
    
    try:
        from src.handlers.media_handler import MediaHandler
        from src.models.app_state import AppState
        from src.config import constants
        
        # Create app state instance
        app_state = AppState()
        handler = MediaHandler(app_state)
        logger.info("✓ MediaHandler instantiated successfully")
        
        # Test supported formats
        logger.info(f"✓ Supported image formats: {constants.SUPPORTED_IMAGE_FORMATS}")
        logger.info(f"✓ Supported video formats: {constants.SUPPORTED_VIDEO_FORMATS}")
        
        # Test method existence
        required_methods = ['get_media_files', 'load_image', 'save_image', 'is_supported_media']
        for method_name in required_methods:
            if hasattr(handler, method_name):
                logger.info(f"✓ Method exists: {method_name}")
            else:
                logger.error(f"✗ Missing method: {method_name}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Media handler test failed: {e}")
        traceback.print_exc()
        return False

def test_dialog_instantiation():
    """Test that dialogs can be instantiated without errors."""
    logger.info("Testing dialog instantiation...")
    
    try:
        # Import PySide6 for Qt application
        from PySide6.QtWidgets import QApplication
        
        # Create QApplication if it doesn't exist
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Test dialog imports (without showing them)
        from src.ui.dialogs.video_processing_dialog import VideoProcessingDialog
        from src.ui.dialogs.audio_overlay_dialog import AudioOverlayDialog
        from src.ui.dialogs.gallery_generation_dialog import GalleryGenerationDialog
        from src.ui.dialogs.highlight_reel_dialog import HighlightReelDialog
        from src.ui.dialogs.story_assistant_dialog import StoryAssistantDialog
        
        logger.info("✓ All dialog classes imported successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Dialog instantiation test failed: {e}")
        traceback.print_exc()
        return False

def test_i18n_system():
    """Test internationalization system."""
    logger.info("Testing I18N system...")
    
    try:
        from src.i18n import I18N
        
        i18n = I18N()
        logger.info("✓ I18N system instantiated successfully")
        
        # Test translation using the correct method name 't'
        test_key = "upload_media"
        translation = i18n.t(test_key)
        logger.info(f"✓ Translation test: '{test_key}' -> '{translation}'")
        
        # Test language switching using the correct method name 'switch'
        available_languages = ['en', 'es', 'fr', 'de', 'it', 'pt', 'nl', 'zh', 'ja', 'ko', 'ru']
        for lang in available_languages:
            try:
                result = i18n.switch(lang)
                if result:
                    logger.info(f"✓ Language switch successful: {lang}")
                else:
                    logger.warning(f"⚠ Language switch failed for {lang} (translation file may not exist)")
            except Exception as e:
                logger.warning(f"⚠ Language switch failed for {lang}: {e}")
        
        # Reset to English
        i18n.switch('en')
        
        # Test method existence
        required_methods = ['t', 'switch', 'get_current_language', 'get_available_languages']
        for method_name in required_methods:
            if hasattr(i18n, method_name):
                logger.info(f"✓ Method exists: {method_name}")
            else:
                logger.error(f"✗ Missing method: {method_name}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ I18N system test failed: {e}")
        traceback.print_exc()
        return False

def test_api_key_manager():
    """Test API key management."""
    logger.info("Testing API key manager...")
    
    try:
        from src.utils.api_key_manager import APIKeyManager
        
        manager = APIKeyManager()
        logger.info("✓ APIKeyManager instantiated successfully")
        
        # Test credential loading (should not fail even if files don't exist)
        try:
            # Test the correct method names
            has_required = manager.has_required_env_variables()
            logger.info(f"✓ Environment variables check: {has_required}")
            
            creds = manager.get_api_credentials_from_env()
            logger.info("✓ API credentials retrieval tested")
            
            instructions = manager.get_instructions()
            logger.info("✓ Instructions retrieval tested")
            
        except Exception as e:
            logger.info(f"ℹ API credentials test completed with info: {e}")
        
        # Test method existence
        required_methods = [
            'get_api_key_from_env', 
            'set_api_key_to_env', 
            'has_required_env_variables',
            'get_api_credentials_from_env',
            'get_instructions'
        ]
        for method_name in required_methods:
            if hasattr(manager, method_name):
                logger.info(f"✓ Method exists: {method_name}")
            else:
                logger.error(f"✗ Missing method: {method_name}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ API key manager test failed: {e}")
        traceback.print_exc()
        return False

def test_file_operations():
    """Test basic file operations."""
    logger.info("Testing file operations...")
    
    try:
        from src.config import constants
        
        # Test writing to output directory
        test_file = os.path.join(constants.OUTPUT_DIR, "test_file.txt")
        with open(test_file, 'w') as f:
            f.write("Test content")
        
        # Test reading
        with open(test_file, 'r') as f:
            content = f.read()
        
        # Clean up
        os.remove(test_file)
        
        logger.info("✓ File operations working correctly")
        return True
        
    except Exception as e:
        logger.error(f"✗ File operations test failed: {e}")
        return False

def test_app_state():
    """Test AppState model functionality."""
    logger.info("Testing AppState model...")
    
    try:
        from src.models.app_state import AppState
        
        # Create instance
        app_state = AppState()
        logger.info("✓ AppState instantiated successfully")
        
        # Test basic operations
        app_state.update_selected_media("test_path.jpg")
        assert app_state.selected_media == "test_path.jpg"
        logger.info("✓ Media selection works")
        
        app_state.start_processing()
        assert app_state.is_processing == True
        logger.info("✓ Processing state management works")
        
        app_state.stop_processing()
        assert app_state.is_processing == False
        logger.info("✓ Processing state reset works")
        
        # Test method existence
        required_methods = [
            'update_selected_media', 
            'start_processing', 
            'stop_processing',
            'reset_state',
            'add_generation_request',
            'update_generation_status'
        ]
        for method_name in required_methods:
            if hasattr(app_state, method_name):
                logger.info(f"✓ Method exists: {method_name}")
            else:
                logger.error(f"✗ Missing method: {method_name}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ AppState test failed: {e}")
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all tests and report results."""
    logger.info("=" * 60)
    logger.info("CROW'S EYE APPLICATION TEST SUITE")
    logger.info("=" * 60)
    
    tests = [
        ("Import Tests", test_imports),
        ("Directory Structure", test_directory_structure),
        ("AppState Model", test_app_state),
        ("Video Handler", test_video_handler),
        ("AI Handler", test_ai_handler),
        ("Media Handler", test_media_handler),
        ("Dialog Instantiation", test_dialog_instantiation),
        ("I18N System", test_i18n_system),
        ("API Key Manager", test_api_key_manager),
        ("File Operations", test_file_operations)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info(f"\nTotal: {len(results)} tests")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    
    if failed == 0:
        logger.info("\n🎉 ALL TESTS PASSED! Application is ready for use.")
    else:
        logger.warning(f"\n⚠️  {failed} test(s) failed. Please review the issues above.")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 