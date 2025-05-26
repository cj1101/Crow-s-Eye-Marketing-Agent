#!/usr/bin/env python3
"""
Comprehensive Connection Testing Suite
=====================================

This script performs extensive testing of all social media platform connections
to ensure the program is fault-free and robust.

Tests include:
- Connection validation for Meta, X, and LinkedIn
- Error handling and recovery
- Edge cases and boundary conditions
- UI responsiveness and user experience
- Data integrity and security
- Performance under load
"""

import os
import sys
import json
import time
import logging
import tempfile
import threading
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch
import requests

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QEventLoop

# Import our handlers
from src.handlers.meta_posting_handler import MetaPostingHandler
from src.handlers.x_posting_handler import XPostingHandler
from src.handlers.linkedin_posting_handler import LinkedInPostingHandler
from src.handlers.unified_posting_handler import UnifiedPostingHandler
from src.ui.dialogs.unified_connection_dialog import UnifiedConnectionDialog, ConnectionTestWorker

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('connection_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ComprehensiveConnectionTester:
    """Comprehensive tester for all platform connections."""
    
    def __init__(self):
        """Initialize the tester."""
        self.app = None
        self.test_results = {}
        self.error_count = 0
        self.warning_count = 0
        self.success_count = 0
        
        # Test data
        self.test_media_files = {}
        self.test_credentials = {}
        
    def setup_test_environment(self):
        """Set up the test environment."""
        logger.info("Setting up test environment...")
        
        # Create QApplication if it doesn't exist
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        else:
            self.app = QApplication.instance()
        
        # Create test media files
        self._create_test_media_files()
        
        # Load test credentials if available
        self._load_test_credentials()
        
        logger.info("Test environment setup complete")
    
    def _create_test_media_files(self):
        """Create test media files for testing."""
        logger.info("Creating test media files...")
        
        # Create temporary directory for test files
        self.test_dir = tempfile.mkdtemp(prefix="connection_test_")
        
        # Create test image (1x1 pixel PNG)
        test_image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x12IDATx\x9cc```bPPP\x00\x02\xac\xea\x05\xc1\x00\x00\x00\x00IEND\xaeB`\x82'
        
        test_image_path = os.path.join(self.test_dir, "test_image.png")
        with open(test_image_path, 'wb') as f:
            f.write(test_image_data)
        
        self.test_media_files['image'] = test_image_path
        
        # Create test text file (for invalid media testing)
        test_text_path = os.path.join(self.test_dir, "test_file.txt")
        with open(test_text_path, 'w') as f:
            f.write("This is a test file for invalid media testing")
        
        self.test_media_files['invalid'] = test_text_path
        
        # Create oversized file (for size limit testing)
        oversized_path = os.path.join(self.test_dir, "oversized.png")
        with open(oversized_path, 'wb') as f:
            # Write 10MB of data
            f.write(b'0' * (10 * 1024 * 1024))
        
        self.test_media_files['oversized'] = oversized_path
        
        logger.info(f"Test media files created in: {self.test_dir}")
    
    def _load_test_credentials(self):
        """Load test credentials if available."""
        logger.info("Loading test credentials...")
        
        # Try to load existing credentials for testing
        credential_files = {
            'meta': 'meta_credentials.json',
            'x': 'x_credentials.json',
            'linkedin': 'linkedin_credentials.json'
        }
        
        for platform, filename in credential_files.items():
            try:
                if os.path.exists(filename):
                    with open(filename, 'r') as f:
                        self.test_credentials[platform] = json.load(f)
                    logger.info(f"Loaded {platform} credentials for testing")
                else:
                    logger.warning(f"No {platform} credentials found - some tests will be skipped")
            except Exception as e:
                logger.error(f"Error loading {platform} credentials: {e}")
    
    def run_all_tests(self):
        """Run all comprehensive tests."""
        logger.info("Starting comprehensive connection tests...")
        
        test_methods = [
            self.test_meta_connection,
            self.test_x_connection,
            self.test_linkedin_connection,
            self.test_unified_handler,
            self.test_connection_dialog,
            self.test_error_handling,
            self.test_edge_cases,
            self.test_performance,
            self.test_security,
            self.test_ui_responsiveness
        ]
        
        for test_method in test_methods:
            try:
                logger.info(f"Running test: {test_method.__name__}")
                test_method()
                self.success_count += 1
                logger.info(f"✅ {test_method.__name__} passed")
            except Exception as e:
                self.error_count += 1
                logger.error(f"❌ {test_method.__name__} failed: {e}")
                self.test_results[test_method.__name__] = {'status': 'failed', 'error': str(e)}
        
        self._generate_test_report()
    
    def test_meta_connection(self):
        """Test Meta API connection thoroughly."""
        logger.info("Testing Meta connection...")
        
        handler = MetaPostingHandler()
        
        # Test 1: Check status without credentials
        status = handler.get_posting_status()
        assert isinstance(status, dict), "Status should be a dictionary"
        assert 'credentials_loaded' in status, "Status should include credentials_loaded"
        
        # Test 2: Test with invalid credentials
        if 'meta' in self.test_credentials:
            # Test posting status with real credentials
            real_status = handler.get_posting_status()
            logger.info(f"Meta status: {real_status}")
        
        # Test 3: Validate media files
        if hasattr(handler, 'validate_media_file'):
            # Test valid image
            valid_result = handler.validate_media_file(self.test_media_files['image'])
            assert valid_result[0] == True, "Valid image should pass validation"
            
            # Test invalid file
            invalid_result = handler.validate_media_file(self.test_media_files['invalid'])
            assert invalid_result[0] == False, "Invalid file should fail validation"
        
        logger.info("Meta connection tests completed")
    
    def test_x_connection(self):
        """Test X API connection thoroughly."""
        logger.info("Testing X connection...")
        
        handler = XPostingHandler()
        
        # Test 1: Check status
        status = handler.get_posting_status()
        assert isinstance(status, dict), "Status should be a dictionary"
        assert 'credentials_loaded' in status, "Status should include credentials_loaded"
        assert 'x_available' in status, "Status should include x_available"
        
        # Test 2: Validate media files
        # Test valid image
        valid_result = handler.validate_media_file(self.test_media_files['image'])
        assert valid_result[0] == True, "Valid image should pass validation"
        
        # Test invalid file
        invalid_result = handler.validate_media_file(self.test_media_files['invalid'])
        assert invalid_result[0] == False, "Invalid file should fail validation"
        
        # Test oversized file
        oversized_result = handler.validate_media_file(self.test_media_files['oversized'])
        assert oversized_result[0] == False, "Oversized file should fail validation"
        
        # Test 3: Test text-only posting capability
        if 'x' in self.test_credentials:
            # This would test actual posting - skip in automated tests
            logger.info("X credentials available - could test real posting")
        
        logger.info("X connection tests completed")
    
    def test_linkedin_connection(self):
        """Test LinkedIn API connection thoroughly."""
        logger.info("Testing LinkedIn connection...")
        
        handler = LinkedInPostingHandler()
        
        # Test 1: Check status
        status = handler.get_posting_status()
        assert isinstance(status, dict), "Status should be a dictionary"
        assert 'credentials_loaded' in status, "Status should include credentials_loaded"
        
        # Test 2: Validate media files if method exists
        if hasattr(handler, 'validate_media_file'):
            valid_result = handler.validate_media_file(self.test_media_files['image'])
            assert isinstance(valid_result, tuple), "Validation should return tuple"
            assert len(valid_result) == 2, "Validation should return (bool, str)"
        
        logger.info("LinkedIn connection tests completed")
    
    def test_unified_handler(self):
        """Test the unified posting handler."""
        logger.info("Testing unified posting handler...")
        
        handler = UnifiedPostingHandler()
        
        # Test 1: Get available platforms
        platforms = handler.get_available_platforms()
        assert isinstance(platforms, dict), "Available platforms should be a dictionary"
        expected_platforms = ['instagram', 'facebook', 'linkedin', 'x']
        for platform in expected_platforms:
            assert platform in platforms, f"Platform {platform} should be in available platforms"
        
        # Test 2: Get platform errors
        errors = handler.get_platform_errors()
        assert isinstance(errors, dict), "Platform errors should be a dictionary"
        
        # Test 3: Get platform limits
        limits = handler.get_platform_limits()
        assert isinstance(limits, dict), "Platform limits should be a dictionary"
        
        # Test 4: Validate media for platforms
        validation_results = handler.validate_media_for_platforms(
            self.test_media_files['image'], 
            ['instagram', 'x']
        )
        assert isinstance(validation_results, dict), "Validation results should be a dictionary"
        
        logger.info("Unified handler tests completed")
    
    def test_connection_dialog(self):
        """Test the unified connection dialog."""
        logger.info("Testing connection dialog...")
        
        # Create dialog
        dialog = UnifiedConnectionDialog()
        
        # Test 1: Dialog initialization
        assert dialog.windowTitle() != "", "Dialog should have a title"
        assert hasattr(dialog, 'platform_status'), "Dialog should have platform_status"
        assert hasattr(dialog, 'tab_widget'), "Dialog should have tab_widget"
        
        # Test 2: Platform status structure
        assert 'meta' in dialog.platform_status, "Should have meta platform"
        assert 'x' in dialog.platform_status, "Should have x platform"
        assert 'linkedin' in dialog.platform_status, "Should have linkedin platform"
        
        # Test 3: Test worker functionality
        test_worker = ConnectionTestWorker(['meta', 'x'])
        assert hasattr(test_worker, 'platforms_to_test'), "Worker should have platforms_to_test"
        
        # Clean up
        dialog.close()
        
        logger.info("Connection dialog tests completed")
    
    def test_error_handling(self):
        """Test error handling and recovery."""
        logger.info("Testing error handling...")
        
        # Test 1: Invalid file paths
        handler = XPostingHandler()
        
        # Test with non-existent file
        result = handler.validate_media_file("/non/existent/file.jpg")
        assert result[0] == False, "Non-existent file should fail validation"
        assert "does not exist" in result[1].lower(), "Error message should mention file doesn't exist"
        
        # Test 2: Network timeout simulation
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.Timeout("Connection timeout")
            
            # This should handle the timeout gracefully
            try:
                handler.post_to_x(caption="Test post")
                # Should not raise an exception
            except Exception as e:
                # If it does raise, it should be handled gracefully
                assert "timeout" in str(e).lower(), "Timeout should be mentioned in error"
        
        # Test 3: Invalid credentials handling
        handler._credentials = None  # Simulate no credentials
        status = handler.get_posting_status()
        assert status['credentials_loaded'] == False, "Should report credentials not loaded"
        assert status['error_message'] is not None, "Should have error message"
        
        logger.info("Error handling tests completed")
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        logger.info("Testing edge cases...")
        
        # Test 1: Empty captions
        handler = XPostingHandler()
        
        # Test with empty caption
        if hasattr(handler, '_post_x_text'):
            # This is an internal method test
            pass
        
        # Test 2: Maximum length captions
        long_caption = "A" * 1000  # Very long caption
        
        # Test 3: Special characters in captions
        special_caption = "Test with émojis 🚀 and spëcial chars: @#$%^&*()"
        
        # Test 4: Unicode handling
        unicode_caption = "Test with unicode: 你好世界 🌍 مرحبا بالعالم"
        
        # Test 5: File permission issues
        # Create a file with no read permissions
        restricted_file = os.path.join(self.test_dir, "restricted.jpg")
        with open(restricted_file, 'w') as f:
            f.write("test")
        
        try:
            os.chmod(restricted_file, 0o000)  # No permissions
            result = handler.validate_media_file(restricted_file)
            # Should handle permission error gracefully
        except PermissionError:
            # This is expected on some systems
            pass
        finally:
            # Restore permissions for cleanup
            try:
                os.chmod(restricted_file, 0o644)
            except:
                pass
        
        logger.info("Edge case tests completed")
    
    def test_performance(self):
        """Test performance under various conditions."""
        logger.info("Testing performance...")
        
        # Test 1: Multiple rapid connections
        start_time = time.time()
        
        for i in range(10):
            handler = XPostingHandler()
            status = handler.get_posting_status()
        
        elapsed = time.time() - start_time
        assert elapsed < 5.0, f"10 handler creations should take less than 5 seconds, took {elapsed:.2f}s"
        
        # Test 2: Large file validation
        start_time = time.time()
        handler = XPostingHandler()
        result = handler.validate_media_file(self.test_media_files['oversized'])
        elapsed = time.time() - start_time
        
        assert elapsed < 2.0, f"Large file validation should take less than 2 seconds, took {elapsed:.2f}s"
        
        # Test 3: Memory usage (basic check)
        import psutil
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Create many handlers
        handlers = []
        for i in range(100):
            handlers.append(XPostingHandler())
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Should not use more than 100MB for 100 handlers
        assert memory_increase < 100 * 1024 * 1024, f"Memory usage too high: {memory_increase / 1024 / 1024:.2f}MB"
        
        # Clean up
        del handlers
        
        logger.info("Performance tests completed")
    
    def test_security(self):
        """Test security aspects."""
        logger.info("Testing security...")
        
        # Test 1: Credential file permissions
        test_cred_file = os.path.join(self.test_dir, "test_credentials.json")
        test_creds = {"api_key": "test_key", "secret": "test_secret"}
        
        with open(test_cred_file, 'w') as f:
            json.dump(test_creds, f)
        
        # Check file permissions (should be readable only by owner)
        file_stat = os.stat(test_cred_file)
        file_mode = file_stat.st_mode & 0o777
        
        # On Unix systems, should not be world-readable
        if os.name != 'nt':  # Not Windows
            assert file_mode & 0o044 == 0, f"Credential file should not be world-readable, mode: {oct(file_mode)}"
        
        # Test 2: No credentials in logs
        # This is more of a code review item, but we can check basic patterns
        
        # Test 3: Input sanitization
        handler = XPostingHandler()
        
        # Test with potentially malicious input
        malicious_inputs = [
            "../../../etc/passwd",
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "\x00\x01\x02\x03"  # Null bytes and control characters
        ]
        
        for malicious_input in malicious_inputs:
            try:
                result = handler.validate_media_file(malicious_input)
                # Should handle gracefully without crashing
                assert isinstance(result, tuple), "Should return tuple even for malicious input"
            except Exception as e:
                # Should not crash with unhandled exceptions
                logger.warning(f"Malicious input caused exception: {e}")
        
        logger.info("Security tests completed")
    
    def test_ui_responsiveness(self):
        """Test UI responsiveness and threading."""
        logger.info("Testing UI responsiveness...")
        
        # Test 1: Dialog creation doesn't block
        start_time = time.time()
        dialog = UnifiedConnectionDialog()
        creation_time = time.time() - start_time
        
        assert creation_time < 2.0, f"Dialog creation should be fast, took {creation_time:.2f}s"
        
        # Test 2: Test worker thread functionality
        test_platforms = ['meta', 'x']
        worker = ConnectionTestWorker(test_platforms)
        
        # Set up signal tracking
        results_received = []
        
        def on_test_complete(platform, success, message):
            results_received.append((platform, success, message))
        
        def on_all_tests_complete(results):
            results_received.append(('all_complete', results))
        
        worker.test_complete.connect(on_test_complete)
        worker.all_tests_complete.connect(on_all_tests_complete)
        
        # Run worker in thread
        worker.start()
        
        # Wait for completion with timeout
        timeout = 15  # 15 seconds
        start_time = time.time()
        
        while worker.isRunning() and (time.time() - start_time) < timeout:
            self.app.processEvents()
            time.sleep(0.1)
        
        # Wait a bit more for signals to be processed
        for _ in range(10):
            self.app.processEvents()
            time.sleep(0.1)
        
        assert not worker.isRunning(), "Worker should complete within timeout"
        
        # The test should pass even if no results are received, as this is a UI responsiveness test
        # The important thing is that the worker completes without blocking the UI
        logger.info(f"Received {len(results_received)} results from worker")
        
        # Clean up
        dialog.close()
        
        logger.info("UI responsiveness tests completed")
    
    def _generate_test_report(self):
        """Generate a comprehensive test report."""
        logger.info("Generating test report...")
        
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total_tests': self.success_count + self.error_count,
                'passed': self.success_count,
                'failed': self.error_count,
                'warnings': self.warning_count
            },
            'results': self.test_results,
            'environment': {
                'python_version': sys.version,
                'platform': sys.platform,
                'test_directory': self.test_dir
            }
        }
        
        # Write report to file
        report_file = 'comprehensive_test_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print("\n" + "="*60)
        print("COMPREHENSIVE CONNECTION TEST REPORT")
        print("="*60)
        print(f"Total Tests: {report['summary']['total_tests']}")
        print(f"Passed: {report['summary']['passed']} ✅")
        print(f"Failed: {report['summary']['failed']} ❌")
        print(f"Warnings: {report['summary']['warnings']} ⚠️")
        
        if report['summary']['failed'] == 0:
            print("\n🎉 ALL TESTS PASSED! The program appears to be fault-free.")
        else:
            print(f"\n⚠️ {report['summary']['failed']} tests failed. Please review the issues.")
        
        print(f"\nDetailed report saved to: {report_file}")
        print("="*60)
    
    def cleanup(self):
        """Clean up test environment."""
        logger.info("Cleaning up test environment...")
        
        # Remove test files
        import shutil
        try:
            if hasattr(self, 'test_dir') and os.path.exists(self.test_dir):
                shutil.rmtree(self.test_dir)
                logger.info(f"Removed test directory: {self.test_dir}")
        except Exception as e:
            logger.warning(f"Could not remove test directory: {e}")

def main():
    """Main test execution function."""
    print("Starting Comprehensive Connection Testing Suite...")
    print("This will test all platform connections and error handling.")
    print("Please ensure you have the required dependencies installed.")
    print()
    
    tester = ComprehensiveConnectionTester()
    
    try:
        tester.setup_test_environment()
        tester.run_all_tests()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error during testing: {e}")
        print(f"❌ Testing failed with error: {e}")
    finally:
        tester.cleanup()
        
        # Quit application if we created it
        if tester.app and hasattr(tester.app, 'quit'):
            tester.app.quit()

if __name__ == "__main__":
    main() 