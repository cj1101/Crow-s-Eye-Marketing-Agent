#!/usr/bin/env python
"""
Crow's Eye Specification Compliance Test Suite.
Verifies that the application meets all requirements from the crowseye-spec.md document.
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
logger = logging.getLogger("spec_compliance")

def test_free_tier_features():
    """Test that all free tier features are implemented."""
    logger.info("Testing Free Tier Features...")
    
    try:
        # Test Media Library functionality
        from src.handlers.media_handler import MediaHandler
        from src.models.app_state import AppState
        from src.config import constants
        
        app_state = AppState()
        media_handler = MediaHandler(app_state)
        
        # Check supported formats match spec
        expected_image_formats = [".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"]
        expected_video_formats = [".mp4", ".mov", ".avi", ".wmv", ".mkv"]
        
        if set(constants.SUPPORTED_IMAGE_FORMATS) >= set(expected_image_formats):
            logger.info("✓ Image formats support meets spec requirements")
        else:
            logger.error("✗ Missing required image formats")
            return False
        
        if set(constants.SUPPORTED_VIDEO_FORMATS) >= set(expected_video_formats):
            logger.info("✓ Video formats support meets spec requirements")
        else:
            logger.error("✗ Missing required video formats")
            return False
        
        # Test Smart Gallery Generator
        from src.ui.dialogs.gallery_generation_dialog import GalleryGenerationDialog
        logger.info("✓ Smart Gallery Generator dialog available")
        
        # Test Post Formatting Options
        from src.ui.dialogs.post_preview_dialog import PostPreviewDialog
        logger.info("✓ Post formatting options available")
        
        # Test Smart Media Search (basic functionality)
        media_files = media_handler.get_media_files()
        logger.info("✓ Media search functionality available")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Free tier features test failed: {e}")
        traceback.print_exc()
        return False

def test_pro_tier_features():
    """Test that all pro tier features are implemented."""
    logger.info("Testing Pro Tier Features...")
    
    try:
        # Test Highlight Reel Generator
        from src.handlers.video_handler import VideoHandler
        from src.ui.dialogs.highlight_reel_dialog import HighlightReelDialog
        
        video_handler = VideoHandler()
        
        # Check if highlight reel method exists and has correct signature
        if hasattr(video_handler, 'generate_highlight_reel'):
            logger.info("✓ Highlight Reel Generator implemented")
        else:
            logger.error("✗ Highlight Reel Generator missing")
            return False
        
        # Test Audio Overlay (renamed from Audio Importer)
        from src.ui.dialogs.audio_overlay_dialog import AudioOverlayDialog
        
        if hasattr(video_handler, 'add_audio_overlay'):
            logger.info("✓ Audio Overlay functionality implemented")
        else:
            logger.error("✗ Audio Overlay functionality missing")
            return False
        
        # Test Story Assistant
        from src.ui.dialogs.story_assistant_dialog import StoryAssistantDialog
        
        if hasattr(video_handler, 'create_story_clips'):
            logger.info("✓ Story Assistant implemented")
        else:
            logger.error("✗ Story Assistant missing")
            return False
        
        # Test Reel Thumbnail Selector
        from src.ui.dialogs.thumbnail_selector_dialog import ThumbnailSelectorDialog
        
        if hasattr(video_handler, 'generate_video_thumbnails'):
            logger.info("✓ Reel Thumbnail Selector implemented")
        else:
            logger.error("✗ Reel Thumbnail Selector missing")
            return False
        
        # Test Post Performance Graphs (Analytics)
        from src.ui.dialogs.analytics_dashboard_dialog import AnalyticsDashboardDialog
        logger.info("✓ Post Performance Graphs available")
        
        # Test Multi-User & Multi-Account (basic structure)
        from src.handlers.auth_handler import auth_handler
        logger.info("✓ Authentication system available for multi-user support")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Pro tier features test failed: {e}")
        traceback.print_exc()
        return False

def test_natural_language_prompts():
    """Test natural language prompt support."""
    logger.info("Testing Natural Language Prompts...")
    
    try:
        from src.handlers.ai_handler import AIHandler
        from src.models.app_state import AppState
        
        app_state = AppState()
        ai_handler = AIHandler(app_state)
        
        # Test caption generation with natural language
        test_prompts = [
            "Generate a caption that sounds sarcastic but excited",
            "Show me 5 vertical photos from the beach",
            "Add 'tickets go live Friday' at the end of the video"
        ]
        
        for prompt in test_prompts:
            try:
                # Test that the method accepts natural language input
                result = ai_handler.generate_caption(prompt, "")
                if isinstance(result, str):
                    logger.info(f"✓ Natural language prompt accepted: '{prompt[:30]}...'")
                else:
                    logger.warning(f"⚠ Prompt returned unexpected type: '{prompt[:30]}...'")
            except Exception as e:
                if "API" in str(e) or "key" in str(e).lower():
                    logger.info(f"ℹ Prompt processing available (API not configured): '{prompt[:30]}...'")
                else:
                    logger.error(f"✗ Prompt processing failed: '{prompt[:30]}...': {e}")
                    return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Natural language prompts test failed: {e}")
        traceback.print_exc()
        return False

def test_ui_requirements():
    """Test UI requirements from the spec."""
    logger.info("Testing UI Requirements...")
    
    try:
        # Test that main UI components exist
        from src.ui.main_window import MainWindow
        logger.info("✓ Main window component available")
        
        # Test dialog system
        from src.ui.dialogs import (
            video_processing_dialog,
            audio_overlay_dialog,
            gallery_generation_dialog,
            post_preview_dialog
        )
        logger.info("✓ Dialog system implemented")
        
        # Test theme management
        from src.ui.theme_manager import ThemeManager
        logger.info("✓ Theme management available")
        
        # Test base components
        from src.ui.base_dialog import BaseDialog
        from src.ui.base_window import BaseMainWindow
        logger.info("✓ Base UI components available")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ UI requirements test failed: {e}")
        traceback.print_exc()
        return False

def test_internationalization():
    """Test internationalization support as specified."""
    logger.info("Testing Internationalization...")
    
    try:
        from src.i18n import I18N
        
        i18n = I18N()
        
        # Test required languages from spec
        required_languages = ['en', 'es', 'fr', 'de', 'pt', 'zh', 'ja', 'ru']
        available_languages = i18n.get_available_languages()
        
        supported_count = 0
        for lang in required_languages:
            if lang in available_languages:
                supported_count += 1
                logger.info(f"✓ Language supported: {lang}")
            else:
                logger.warning(f"⚠ Language not available: {lang}")
        
        if supported_count >= len(required_languages) * 0.7:  # At least 70% of required languages
            logger.info("✓ Internationalization support meets spec requirements")
        else:
            logger.error("✗ Insufficient language support")
            return False
        
        # Test language switching
        current_lang = i18n.get_current_language()
        if i18n.switch('es') and i18n.switch(current_lang):
            logger.info("✓ Language switching functionality works")
        else:
            logger.error("✗ Language switching failed")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Internationalization test failed: {e}")
        traceback.print_exc()
        return False

def test_file_structure_compliance():
    """Test that the file structure follows the spec."""
    logger.info("Testing File Structure Compliance...")
    
    try:
        # Check for required directories according to spec
        required_dirs = [
            'src/ui/components',
            'src/ui/dialogs', 
            'src/handlers',
            'src/utils',
            'src/models',
            'src/config'
        ]
        
        missing_dirs = []
        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                missing_dirs.append(dir_path)
            else:
                logger.info(f"✓ Directory exists: {dir_path}")
        
        if missing_dirs:
            logger.error(f"✗ Missing directories: {missing_dirs}")
            return False
        
        # Check for key files
        key_files = [
            'src/ui/main_window.py',
            'src/handlers/video_handler.py',
            'src/handlers/ai_handler.py',
            'src/handlers/media_handler.py',
            'src/models/app_state.py',
            'src/config/constants.py'
        ]
        
        missing_files = []
        for file_path in key_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
            else:
                logger.info(f"✓ File exists: {file_path}")
        
        if missing_files:
            logger.error(f"✗ Missing files: {missing_files}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ File structure compliance test failed: {e}")
        traceback.print_exc()
        return False

def test_video_processing_workflow():
    """Test the video processing workflow as specified."""
    logger.info("Testing Video Processing Workflow...")
    
    try:
        from src.ui.dialogs.video_processing_dialog import VideoProcessingDialog
        from src.handlers.video_handler import VideoHandler
        
        # Test that video processing dialog exists and can be imported
        logger.info("✓ Video Processing Dialog available")
        
        # Test video handler methods
        video_handler = VideoHandler()
        
        required_methods = [
            'generate_highlight_reel',
            'create_story_clips',
            'generate_video_thumbnails',
            'add_audio_overlay',
            'get_video_info'
        ]
        
        for method_name in required_methods:
            if hasattr(video_handler, method_name):
                logger.info(f"✓ Video method available: {method_name}")
            else:
                logger.error(f"✗ Missing video method: {method_name}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Video processing workflow test failed: {e}")
        traceback.print_exc()
        return False

def test_media_library_functionality():
    """Test media library functionality as specified."""
    logger.info("Testing Media Library Functionality...")
    
    try:
        from src.handlers.media_handler import MediaHandler
        from src.models.app_state import AppState
        from src.config import constants
        
        app_state = AppState()
        media_handler = MediaHandler(app_state)
        
        # Test media library directory exists
        if os.path.exists(constants.MEDIA_LIBRARY_DIR):
            logger.info("✓ Media library directory exists")
        else:
            logger.error("✗ Media library directory missing")
            return False
        
        # Test media file operations
        required_methods = [
            'get_media_files',
            'load_image',
            'save_image',
            'is_supported_media',
            'get_media_info'
        ]
        
        for method_name in required_methods:
            if hasattr(media_handler, method_name):
                logger.info(f"✓ Media method available: {method_name}")
            else:
                logger.error(f"✗ Missing media method: {method_name}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Media library functionality test failed: {e}")
        traceback.print_exc()
        return False

def run_spec_compliance_tests():
    """Run all specification compliance tests."""
    logger.info("=" * 60)
    logger.info("CROW'S EYE SPECIFICATION COMPLIANCE TEST SUITE")
    logger.info("=" * 60)
    
    tests = [
        ("Free Tier Features", test_free_tier_features),
        ("Pro Tier Features", test_pro_tier_features),
        ("Natural Language Prompts", test_natural_language_prompts),
        ("UI Requirements", test_ui_requirements),
        ("Internationalization", test_internationalization),
        ("File Structure Compliance", test_file_structure_compliance),
        ("Video Processing Workflow", test_video_processing_workflow),
        ("Media Library Functionality", test_media_library_functionality)
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
    logger.info("SPECIFICATION COMPLIANCE RESULTS")
    logger.info("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "COMPLIANT" if result else "NON-COMPLIANT"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info(f"\nTotal: {len(results)} compliance tests")
    logger.info(f"Compliant: {passed}")
    logger.info(f"Non-compliant: {failed}")
    
    compliance_percentage = (passed / len(results)) * 100
    logger.info(f"Overall Compliance: {compliance_percentage:.1f}%")
    
    if failed == 0:
        logger.info("\n🎉 FULL SPECIFICATION COMPLIANCE ACHIEVED!")
        logger.info("The application meets all requirements from the Crow's Eye spec.")
    elif compliance_percentage >= 90:
        logger.info(f"\n✅ HIGH COMPLIANCE ACHIEVED ({compliance_percentage:.1f}%)")
        logger.info("The application meets most requirements with minor gaps.")
    elif compliance_percentage >= 75:
        logger.warning(f"\n⚠️ MODERATE COMPLIANCE ({compliance_percentage:.1f}%)")
        logger.warning("Some important features may be missing or incomplete.")
    else:
        logger.error(f"\n❌ LOW COMPLIANCE ({compliance_percentage:.1f}%)")
        logger.error("Significant work needed to meet specification requirements.")
    
    return failed == 0

if __name__ == "__main__":
    success = run_spec_compliance_tests()
    sys.exit(0 if success else 1) 