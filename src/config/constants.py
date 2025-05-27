"""
Application constants and configuration values.
Consolidated from various versioned constant files.
"""
import os
import logging
from pathlib import Path

# Version
APP_VERSION = "5.0.0"

# Directories
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_DIR = os.path.join(ROOT_DIR, 'data')
MEDIA_LIBRARY_DIR = os.path.join(ROOT_DIR, 'media_library')
OUTPUT_DIR = os.path.join(ROOT_DIR, 'output')
KNOWLEDGE_BASE_DIR = os.path.join(ROOT_DIR, 'knowledge_base')
LIBRARY_DIR = os.path.join(ROOT_DIR, 'library')
LIBRARY_IMAGES_DIR = os.path.join(LIBRARY_DIR, 'images')
LIBRARY_DATA_DIR = os.path.join(LIBRARY_DIR, 'data')
MEDIA_GALLERY_DIR = os.path.join(ROOT_DIR, 'media_gallery')

# Files
PRESETS_FILE = os.path.join(ROOT_DIR, 'presets.json')
META_CREDENTIALS_FILE = os.path.join(ROOT_DIR, 'meta_credentials.json')
META_CREDENTIALS_TEMPLATE_FILE = os.path.join(ROOT_DIR, 'meta_credentials_template.json')
MEDIA_STATUS_FILE = os.path.join(ROOT_DIR, 'media_status.json')
CLOUD_STORAGE_CONFIG_FILE = os.path.join(ROOT_DIR, 'cloud_storage_config.json')

# Logging
LOG_LEVEL = logging.INFO
LOG_FILE = "app_log.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# UI Constants
UI_REFRESH_INTERVAL = 5000  # milliseconds
THUMBNAIL_SIZE = (200, 200)
PREVIEW_MAX_SIZE = (800, 800)

# Media Handling
SUPPORTED_IMAGE_FORMATS = [".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"]
SUPPORTED_VIDEO_FORMATS = [".mp4", ".mov", ".avi", ".wmv", ".mkv"]
SUPPORTED_AUDIO_FORMATS = [".mp3", ".wav", ".aac", ".m4a", ".ogg", ".flac"]
SUPPORTED_MEDIA_FORMATS = SUPPORTED_IMAGE_FORMATS + SUPPORTED_VIDEO_FORMATS + SUPPORTED_AUDIO_FORMATS

MAX_IMAGE_SIZE = 8 * 1024 * 1024  # 8MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB
MAX_AUDIO_SIZE = 25 * 1024 * 1024  # 25MB
MAX_VIDEO_DURATION = 60 * 15  # 15 minutes (in seconds)
MAX_AUDIO_DURATION = 60 * 10  # 10 minutes (in seconds)

# Instagram Limits
IG_MAX_CAPTION_LENGTH = 2200
IG_MAX_HASHTAGS = 30
IG_MAX_MENTIONS = 20
IG_MAX_IMAGE_SIZE = (1080, 1350)  # pixels
IG_MIN_IMAGE_SIZE = (320, 320)  # pixels
IG_ASPECT_RATIO_MIN = 4 / 5  # width/height
IG_ASPECT_RATIO_MAX = 1.91  # width/height

# Knowledge Base
MAX_KNOWLEDGE_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Library Settings
MAX_LIBRARY_ITEMS = 10000

# --- Application Paths ---
MEDIA_LIBRARY_DIR = os.path.join(ROOT_DIR, "media_library")
LIBRARY_DIR = os.path.join(ROOT_DIR, "library")
OUTPUT_DIR = os.path.join(ROOT_DIR, "output")
DOCS_DIR = os.path.join(ROOT_DIR, "docs")

# --- File Paths ---
MEDIA_STATUS_FILE = os.path.join(ROOT_DIR, "media_status.json")
PRESETS_FILE = os.path.join(ROOT_DIR, "presets.json")
CLOUD_CONFIG_FILE = os.path.join(ROOT_DIR, "cloud_storage_config.json")

# --- Media Types ---
SUPPORTED_IMAGE_TYPES = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
SUPPORTED_VIDEO_TYPES = {'.mp4', '.mov', '.avi', '.webm'}
SUPPORTED_MEDIA_TYPES = SUPPORTED_IMAGE_TYPES | SUPPORTED_VIDEO_TYPES

# --- Media Processing ---
THUMBNAIL_SIZE = (200, 200)  # Width, Height
MAX_PREVIEW_SIZE = (1200, 800)
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB

# --- Status Constants ---
STATUS_KEY_GENERATION = "generation"
STATUS_KEY_POSTED_IG = "posted_to_instagram"
STATUS_KEY_POSTED_IG_TS = "posted_to_instagram_timestamp"
STATUS_KEY_POSTED_FB = "posted_to_facebook"
STATUS_KEY_POSTED_FB_TS = "posted_to_facebook_timestamp"
STATUS_KEY_SCHEDULED = "scheduled"
STATUS_KEY_SCHEDULED_TIME = "scheduled_time"
STATUS_KEY_SCHEDULED_PLATFORM = "scheduled_platform"
STATUS_KEY_ERROR = "error_message"
STATUS_KEY_METADATA = "metadata"

STATUS_VAL_OK = "ok"
STATUS_VAL_SUCCESS = "success"
STATUS_VAL_FAILED = "failed"
STATUS_VAL_PENDING = "pending"
STATUS_VAL_IN_PROGRESS = "in_progress"

DEFAULT_MEDIA_STATUS_ENTRY = {
    STATUS_KEY_GENERATION: STATUS_VAL_OK,
    STATUS_KEY_POSTED_IG: False,
    STATUS_KEY_POSTED_IG_TS: None,
    STATUS_KEY_POSTED_FB: False,
    STATUS_KEY_POSTED_FB_TS: None,
    STATUS_KEY_SCHEDULED: False,
    STATUS_KEY_SCHEDULED_TIME: None,
    STATUS_KEY_SCHEDULED_PLATFORM: None,
    STATUS_KEY_ERROR: None,
    STATUS_KEY_METADATA: {}
}

# --- UI Constants ---
UI_REFRESH_INTERVAL = 1000  # milliseconds
UI_MAX_RECENT_ITEMS = 10
UI_TOOLTIP_DELAY = 500  # milliseconds

# --- API Constants ---
META_API_VERSION = "v18.0"
META_API_BASE_URL = f"https://graph.facebook.com/{META_API_VERSION}"
META_API_TIMEOUT = 30  # seconds
META_API_MAX_RETRIES = 3

# --- Logging ---
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = os.path.join(ROOT_DIR, "app_log.log")
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# --- Threading ---
MAX_WORKER_THREADS = 4
TASK_QUEUE_SIZE = 100

# --- Cache ---
CACHE_ENABLED = True
CACHE_MAX_SIZE = 1000
CACHE_TTL = 3600  # 1 hour in seconds

# --- Error Messages ---
ERROR_MESSAGES = {
    "file_not_found": "File not found: {}",
    "invalid_credentials": "Invalid or missing Meta API credentials",
    "api_error": "Meta API error: {}",
    "upload_failed": "Failed to upload media: {}",
    "invalid_media": "Unsupported media type: {}",
    "permission_denied": "Permission denied: {}",
    "network_error": "Network error: {}",
    "timeout": "Operation timed out",
    "unknown_error": "An unexpected error occurred: {}"
}

# --- Success Messages ---
SUCCESS_MESSAGES = {
    "upload_complete": "Successfully uploaded {}",
    "status_updated": "Status updated successfully",
    "credentials_loaded": "Meta credentials loaded successfully",
    "media_processed": "Media processed successfully",
    "cache_cleared": "Cache cleared successfully"
}

# --- Feature Flags ---
FEATURES = {
    "enable_auto_refresh": True,
    "enable_cloud_storage": False,
    "enable_advanced_editing": True,
    "enable_batch_processing": True,
    "enable_analytics": False
}

# --- Validation ---
VALIDATION = {
    "min_image_dimensions": (100, 100),
    "max_image_dimensions": (4096, 4096),
    "min_video_duration": 1,  # seconds
    "max_video_duration": 60,  # seconds
    "allowed_image_formats": SUPPORTED_IMAGE_TYPES,
    "allowed_video_formats": SUPPORTED_VIDEO_TYPES,
    "max_file_size": MAX_UPLOAD_SIZE
}

# Default system prompt for AI generation
DEFAULT_SYSTEM_PROMPT = """
You are an expert social media marketing assistant for Breadsmith, a premium artisan bakery.
Your task is to generate engaging, conversational captions for social media posts.
The captions should be friendly, warm, and inviting - like a local baker talking to their community.
Emphasize quality ingredients, traditional methods, and the craft of baking.
Use a consistent, approachable tone that reflects Breadsmith's premium but accessible brand.
Include relevant hashtags that would appeal to bread enthusiasts and local food communities.
Keep captions between 150-280 characters (excluding hashtags) to work well across platforms.
Avoid overused phrases and clichés. Make each caption unique and specific to the image.
Don't use emoji symbols unless specifically requested.
"""

# Default instructions for first-time users
DEFAULT_INSTRUCTIONS = """
Describe this bread/baked good for a social media post.
Focus on texture, ingredients, and what makes it special.
Use a warm, friendly tone as if talking to a regular customer.
Include appropriate hashtags at the end.
"""

# Default placeholder text for instructions
INSTRUCTIONS_PLACEHOLDER = "Enter instructions for the AI..."

# Default placeholder text for captions
CAPTION_PLACEHOLDER = "Generated captions will appear here..."

# File dialog filters
IMAGE_FILTER = "Image Files (*.jpg *.jpeg *.png)"
VIDEO_FILTER = "Video Files (*.mp4 *.mov *.avi)"
MEDIA_FILTER = "Media Files (*.jpg *.jpeg *.png *.mp4 *.mov *.avi)"
CONTEXT_FILTER = "Text Files (*.txt *.doc *.docx *.pdf)"
ALL_FILES_FILTER = "All Files (*)"

# UI labels and messages
UI_TITLE = "Automated Marketing System"
UI_DEFAULT_STATUS = "Ready"

# File paths
APP_LOG_PATH = "app.log"
MEDIA_STATUS_PATH = "media_status.json"
LIBRARY_DATA_PATH = "library/data/library.json"
LIBRARY_IMAGES_PATH = "library/images"

# API configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Toast notification duration (milliseconds)
TOAST_DURATION_SHORT = 2000
TOAST_DURATION_NORMAL = 3000
TOAST_DURATION_LONG = 5000

# Instagram defaults
INSTAGRAM_SYSTEM_PROMPT = """
You are an expert Instagram marketing assistant for Breadsmith, a premium artisan bakery.
Your task is to generate engaging captions for Instagram that will lead to high engagement.
Use a conversational, authentic tone that feels like a real person at a local bakery talking to followers.
The captions should be friendly, inviting, and communicate Breadsmith's passion for quality baking.
Focus on seasonal themes, quality ingredients, and the craft of traditional baking methods.
Include 5-8 relevant hashtags that would appeal to bread lovers and local food communities.
Keep the main caption between 150-220 characters to ensure good readability on mobile devices.
Avoid overly promotional language or salesy terms. Be conversational and authentic.
Occasionally include a call to action like "Tag someone who would love this" or "What's your favorite bread?"
"""

# Error messages
ERROR_NO_FILE_SELECTED = "No file selected"
ERROR_FILE_NOT_FOUND = "File not found"
ERROR_INVALID_FILE_TYPE = "Invalid file type"
ERROR_API_CONNECTION = "Could not connect to API"
ERROR_PROCESSING = "Error processing request"

# Crow's Eye settings
CROWSEYE_SETTINGS = {
    'auto_enhance': True,
    'max_gallery_items': 10,
}

# --- Default font path ---
DEFAULT_FONT_PATH = os.path.join(os.path.dirname(__file__), 'fonts', 'opensans.ttf')

# --- API Settings ---
MAX_API_RETRIES = 3
API_RETRY_SLEEP = 1

# --- UI Settings ---
DEFAULT_UI_SETTINGS = {
    'theme': 'light',
    'font_size': 'medium',
} 