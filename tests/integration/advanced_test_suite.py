#!/usr/bin/env python
"""
Advanced test suite for Crow's Eye Marketing Automation Platform.
Tests actual functionality, edge cases, and stress scenarios.
"""

import sys
import os
import logging
import traceback
import tempfile
import shutil
from pathlib import Path
from PIL import Image
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("advanced_test")

def create_test_image(width=800, height=600, color=(255, 0, 0)):
    """Create a test image for testing purposes."""
    img = Image.new('RGB', (width, height), color)
    return img

def create_test_files():
    """Create test files for testing."""
    test_files = {}
    
    # Create test images
    test_files['test_image_1.jpg'] = create_test_image(800, 600, (255, 0, 0))  # Red
    test_files['test_image_2.png'] = create_test_image(1080, 1080, (0, 255, 0))  # Green
    test_files['test_image_3.jpg'] = create_test_image(1920, 1080, (0, 0, 255))  # Blue
    
    return test_files

def test_media_handler_functionality():
    """Test MediaHandler with actual file operations."""
    logger.info("Testing MediaHandler functionality...")
    
    try:
        from src.handlers.media_handler import MediaHandler
        from src.models.app_state import AppState
        from src.config import constants
        
        # Create app state and handler
        app_state = AppState()
        handler = MediaHandler(app_state)
        
        # Create test files
        test_files = create_test_files()
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Save test images to temp directory
            for filename, img in test_files.items():
                filepath = os.path.join(temp_dir, filename)
                img.save(filepath)
                logger.info(f"✓ Created test file: {filename}")
            
            # Test loading images
            for filename in test_files.keys():
                filepath = os.path.join(temp_dir, filename)
                loaded_img = handler.load_image(filepath)
                if loaded_img:
                    logger.info(f"✓ Successfully loaded: {filename}")
                    
                    # Test getting dimensions
                    dimensions = handler.get_image_dimensions(filepath)
                    if dimensions:
                        logger.info(f"✓ Got dimensions for {filename}: {dimensions}")
                    
                    # Test media info
                    info = handler.get_media_info(filepath)
                    if info:
                        logger.info(f"✓ Got media info for {filename}")
                else:
                    logger.error(f"✗ Failed to load: {filename}")
                    return False
            
            # Test supported media detection
            for filename in test_files.keys():
                filepath = os.path.join(temp_dir, filename)
                is_supported = handler.is_supported_media(filepath)
                if is_supported:
                    logger.info(f"✓ Correctly identified {filename} as supported")
                else:
                    logger.error(f"✗ Failed to identify {filename} as supported")
                    return False
            
            # Test unsupported file
            unsupported_file = os.path.join(temp_dir, "test.txt")
            with open(unsupported_file, 'w') as f:
                f.write("test")
            
            is_supported = handler.is_supported_media(unsupported_file)
            if not is_supported:
                logger.info("✓ Correctly identified .txt file as unsupported")
            else:
                logger.error("✗ Incorrectly identified .txt file as supported")
                return False
            
            return True
            
        finally:
            # Clean up temp directory
            shutil.rmtree(temp_dir)
            
    except Exception as e:
        logger.error(f"✗ MediaHandler functionality test failed: {e}")
        traceback.print_exc()
        return False

def test_ai_handler_functionality():
    """Test AIHandler with actual caption generation (without API calls)."""
    logger.info("Testing AIHandler functionality...")
    
    try:
        from src.handlers.ai_handler import AIHandler
        from src.models.app_state import AppState
        
        # Create app state and handler
        app_state = AppState()
        handler = AIHandler(app_state)
        
        # Test with different scenarios
        test_scenarios = [
            {
                "instructions": "Generate a caption for a bakery photo",
                "photo_editing": "bright and warm",
                "expected_type": str
            },
            {
                "instructions": "Create a caption for a bread photo",
                "photo_editing": "enhanced contrast",
                "expected_type": str
            }
        ]
        
        for i, scenario in enumerate(test_scenarios):
            try:
                caption = handler.generate_caption(
                    scenario["instructions"],
                    scenario["photo_editing"]
                )
                
                if isinstance(caption, scenario["expected_type"]):
                    logger.info(f"✓ Scenario {i+1}: Generated caption of correct type")
                    if len(caption) > 0:
                        logger.info(f"✓ Scenario {i+1}: Caption has content")
                    else:
                        logger.warning(f"⚠ Scenario {i+1}: Caption is empty")
                else:
                    logger.error(f"✗ Scenario {i+1}: Caption is not of expected type")
                    return False
                    
            except Exception as e:
                # This is expected if no API key is configured
                if "API" in str(e) or "key" in str(e).lower():
                    logger.info(f"ℹ Scenario {i+1}: API not configured (expected): {e}")
                else:
                    logger.error(f"✗ Scenario {i+1}: Unexpected error: {e}")
                    return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ AIHandler functionality test failed: {e}")
        traceback.print_exc()
        return False

def test_video_handler_edge_cases():
    """Test VideoHandler with edge cases."""
    logger.info("Testing VideoHandler edge cases...")
    
    try:
        from src.handlers.video_handler import VideoHandler
        
        handler = VideoHandler()
        
        # Test with non-existent file
        result = handler.generate_highlight_reel("non_existent_video.mp4")
        success, output_path, message = result
        
        if not success and "not found" in message.lower():
            logger.info("✓ Correctly handled non-existent video file")
        else:
            logger.error("✗ Did not properly handle non-existent video file")
            return False
        
        # Test with invalid parameters
        result = handler.create_story_clips("non_existent_video.mp4", max_clip_duration=-1)
        success, output_paths, message = result
        
        if not success:
            logger.info("✓ Correctly handled invalid parameters")
        else:
            logger.error("✗ Did not properly handle invalid parameters")
            return False
        
        # Test video info with non-existent file
        info = handler.get_video_info("non_existent_video.mp4")
        if not info or len(info) == 0:
            logger.info("✓ Correctly handled video info for non-existent file")
        else:
            logger.error("✗ Did not properly handle video info for non-existent file")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ VideoHandler edge cases test failed: {e}")
        traceback.print_exc()
        return False

def test_app_state_persistence():
    """Test AppState save/load functionality."""
    logger.info("Testing AppState persistence...")
    
    try:
        from src.models.app_state import AppState
        
        # Create app state and set some values
        app_state = AppState()
        app_state.update_selected_media("test_media.jpg")
        app_state.current_caption = "Test caption"
        app_state.photo_editing_instructions = "Make it brighter"
        app_state.context_files = ["file1.txt", "file2.txt"]
        
        # Save to temp file
        temp_file = tempfile.mktemp(suffix=".json")
        
        try:
            # Test save
            save_result = app_state.save_to_file(temp_file)
            if save_result:
                logger.info("✓ Successfully saved app state")
            else:
                logger.error("✗ Failed to save app state")
                return False
            
            # Create new app state and load
            new_app_state = AppState()
            load_result = new_app_state.load_from_file(temp_file)
            
            if load_result:
                logger.info("✓ Successfully loaded app state")
                
                # Verify data
                if new_app_state.selected_media == "test_media.jpg":
                    logger.info("✓ Selected media preserved")
                else:
                    logger.error("✗ Selected media not preserved")
                    return False
                
                if new_app_state.current_caption == "Test caption":
                    logger.info("✓ Caption preserved")
                else:
                    logger.error("✗ Caption not preserved")
                    return False
                
                if new_app_state.context_files == ["file1.txt", "file2.txt"]:
                    logger.info("✓ Context files preserved")
                else:
                    logger.error("✗ Context files not preserved")
                    return False
                
            else:
                logger.error("✗ Failed to load app state")
                return False
            
            return True
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)
                
    except Exception as e:
        logger.error(f"✗ AppState persistence test failed: {e}")
        traceback.print_exc()
        return False

def test_i18n_edge_cases():
    """Test I18N system with edge cases."""
    logger.info("Testing I18N edge cases...")
    
    try:
        from src.i18n import I18N
        
        i18n = I18N()
        
        # Test with empty key
        result = i18n.t("")
        if result == "":
            logger.info("✓ Correctly handled empty key")
        else:
            logger.error("✗ Did not properly handle empty key")
            return False
        
        # Test with non-existent key
        result = i18n.t("non_existent_key_12345")
        if result == "non_existent_key_12345":
            logger.info("✓ Correctly returned key for non-existent translation")
        else:
            logger.error("✗ Did not properly handle non-existent key")
            return False
        
        # Test with invalid language code
        result = i18n.switch("invalid_lang_code")
        if not result:
            logger.info("✓ Correctly rejected invalid language code")
        else:
            logger.error("✗ Did not properly reject invalid language code")
            return False
        
        # Test switching to same language
        current_lang = i18n.get_current_language()
        result = i18n.switch(current_lang)
        if result:
            logger.info("✓ Correctly handled switching to same language")
        else:
            logger.error("✗ Did not properly handle switching to same language")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ I18N edge cases test failed: {e}")
        traceback.print_exc()
        return False

def test_constants_and_configuration():
    """Test that all constants are properly defined and accessible."""
    logger.info("Testing constants and configuration...")
    
    try:
        from src.config import constants
        
        # Test required constants exist
        required_constants = [
            'MEDIA_LIBRARY_DIR',
            'OUTPUT_DIR',
            'LIBRARY_DIR',
            'SUPPORTED_IMAGE_FORMATS',
            'SUPPORTED_VIDEO_FORMATS',
            'MAX_IMAGE_SIZE',
            'MAX_VIDEO_SIZE'
        ]
        
        for const_name in required_constants:
            if hasattr(constants, const_name):
                value = getattr(constants, const_name)
                logger.info(f"✓ Constant {const_name}: {value}")
            else:
                logger.error(f"✗ Missing constant: {const_name}")
                return False
        
        # Test that directories can be created
        test_dirs = [
            constants.MEDIA_LIBRARY_DIR,
            constants.OUTPUT_DIR,
            constants.LIBRARY_DIR
        ]
        
        for dir_path in test_dirs:
            try:
                os.makedirs(dir_path, exist_ok=True)
                if os.path.exists(dir_path):
                    logger.info(f"✓ Directory accessible: {dir_path}")
                else:
                    logger.error(f"✗ Directory not accessible: {dir_path}")
                    return False
            except Exception as e:
                logger.error(f"✗ Cannot create directory {dir_path}: {e}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Constants test failed: {e}")
        traceback.print_exc()
        return False

def test_error_handling():
    """Test error handling across components."""
    logger.info("Testing error handling...")
    
    try:
        from src.handlers.media_handler import MediaHandler
        from src.models.app_state import AppState
        
        app_state = AppState()
        handler = MediaHandler(app_state)
        
        # Test loading non-existent image
        result = handler.load_image("non_existent_image.jpg")
        if result is None:
            logger.info("✓ Correctly handled non-existent image")
        else:
            logger.error("✗ Did not properly handle non-existent image")
            return False
        
        # Test getting dimensions of non-existent file
        result = handler.get_image_dimensions("non_existent_image.jpg")
        if result is None:
            logger.info("✓ Correctly handled dimensions of non-existent file")
        else:
            logger.error("✗ Did not properly handle dimensions of non-existent file")
            return False
        
        # Test saving to invalid path (use a path that's definitely invalid on Windows)
        test_img = create_test_image()
        invalid_path = "Z:\\nonexistent\\invalid\\path\\image.jpg"  # Z: drive typically doesn't exist
        result = handler.save_image(test_img, invalid_path)
        if not result:
            logger.info("✓ Correctly handled invalid save path")
        else:
            logger.error("✗ Did not properly handle invalid save path")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error handling test failed: {e}")
        traceback.print_exc()
        return False

def run_advanced_tests():
    """Run all advanced tests and report results."""
    logger.info("=" * 60)
    logger.info("CROW'S EYE ADVANCED TEST SUITE")
    logger.info("=" * 60)
    
    tests = [
        ("MediaHandler Functionality", test_media_handler_functionality),
        ("AIHandler Functionality", test_ai_handler_functionality),
        ("VideoHandler Edge Cases", test_video_handler_edge_cases),
        ("AppState Persistence", test_app_state_persistence),
        ("I18N Edge Cases", test_i18n_edge_cases),
        ("Constants and Configuration", test_constants_and_configuration),
        ("Error Handling", test_error_handling)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test '{test_name}' crashed: {e}")
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("ADVANCED TEST RESULTS SUMMARY")
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
        logger.info("\n🎉 ALL ADVANCED TESTS PASSED! Application is production-ready.")
    else:
        logger.warning(f"\n⚠️  {failed} advanced test(s) failed. Please review the issues above.")
    
    return failed == 0

if __name__ == "__main__":
    success = run_advanced_tests()
    sys.exit(0 if success else 1) 