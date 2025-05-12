# Breadsmith Marketing Tool

A comprehensive social media management tool for Breadsmith, designed to streamline media handling, editing, and posting to Instagram.

## Features

- **Media Management**
  - Upload and organize media files
  - Generate thumbnails and previews
  - Track media status and posting history
  - Support for images and videos

- **Photo Editing**
  - Basic image enhancements
  - Special effects (warm tone, sepia, vintage, vignette)
  - Batch processing capabilities
  - Preview before posting

- **Instagram Integration**
  - Direct posting to Instagram Business
  - Status tracking and history
  - Meta API integration
  - Credential management

- **Post Scheduling**
  - Schedule posts for future publication
  - Create weekly posting schedules with customizable times
  - Queue posts to publish in order
  - Automatic posting based on schedule
  - Platform targeting (Instagram, Facebook, or both)

- **User Interface**
  - Modern PyQt6-based interface
  - Real-time preview
  - Status updates and notifications
  - Auto-refresh capability

- **Content Generation**: 
  - AI-powered caption generation for social media posts
  - Gemini AI integration for intelligent image content analysis
  - Context-aware captions that connect image content to business context

- **Knowledge Base**: Store and access important business information 
- **Comment Management**: View and respond to comments and direct messages
- **Meta Insights**: View business analytics from your Meta Business account

## AI-Powered Image Analysis and Caption Generation

The tool now exclusively uses Google's Gemini AI to analyze image content and generate engaging captions:

- **Advanced AI Models**: Uses the latest Gemini 1.5 Flash models for both vision and text generation
- **Smart Image Content Analysis**: Gemini analyzes what's actually in your images (people, objects, scenes, activities) rather than just technical aspects
- **Context-Aware Captions**: Connects the image content to your business context files for highly relevant captions
- **Thematic Understanding**: Recognizes themes and concepts in images for more meaningful captions
- **Natural Language**: Generates conversational, engaging captions with appropriate hashtags

To use this feature:
1. Get a Google Gemini API key from https://makersuite.google.com/app/apikey
2. Copy `.env.example` to `.env` and add your Gemini API key
3. Use the caption generation feature as normal - it will now leverage Gemini's capabilities

## Meta Insights Feature

The new Meta Insights dashboard provides a comprehensive view of your business's performance on Meta platforms (Facebook and Instagram). The dashboard displays:

- Page views, reach, and engagement metrics
- Audience demographics and growth trends
- Content performance analytics
- Reaction analysis
- Video performance metrics

To use this feature, you must have:
1. A Meta Business account
2. The appropriate API access tokens configured
3. Connected your page through the login process

The insights are organized into four tabs:
- **Overview**: Summary of key metrics
- **Engagement**: Detailed engagement analysis
- **Audience**: Demographics and follower information
- **Content Performance**: Analysis of post performance

## Installation

1. **Prerequisites**
   - Python 3.8 or higher
   - Git (for cloning the repository)
   - Google Gemini API key (for image analysis and caption generation)
   - Meta Business account (optional, for Instagram/Facebook integration)

2. **Setup**
   ```bash
   # Clone the repository
   git clone https://github.com/yourusername/breadsmith_marketing.git
   cd breadsmith_marketing

   # Create and activate virtual environment
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac

   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Configuration**
   - Copy `.env.example` to `.env` and add your Gemini API key
   - Copy `meta_credentials_template.json` to `meta_credentials.json` (if using Meta API)
   - Fill in your Meta API credentials (if using Meta API)
   - Create necessary directories (they will be created automatically on first run)

## Usage

1. **Starting the Application**
   ```bash
   # Run the application (scheduling is always enabled)
   python run.py
   
   # Or use the batch files on Windows
   run_app.bat
   run_with_schedule.bat   # Alternative batch file
   ```

2. **Basic Operations**
   - Use the "Upload Media" button to add new files
   - Select a file to preview and edit
   - Apply edits using the edit options
   - Post directly to Instagram using the "Post" button

3. **Scheduling Posts**
   - Navigate to the "Schedule" tab
   - Click "Add Schedule" to create a new posting schedule
   - Set frequency, days, and times for posting
   - Choose between basic or advanced scheduling
   - Posts will be automatically published at scheduled times
   - Create multiple schedules for different content types

4. **Social Media Posting**
   - Post directly to Instagram/Facebook from the library/preview
   - Choose platform(s) when posting (Instagram, Facebook, or both)
   - Schedule individual posts or create recurring schedules

5. **Media Management**
   - All media files are stored in the `media_library` directory
   - Status and history are tracked in `media_status.json`
   - Thumbnails are generated automatically

6. **Meta API Setup**
   - Requires a Meta Business account
   - Instagram Business account connected to Facebook Page
   - Valid API credentials in `meta_credentials.json`

## Development

1. **Project Structure**
   ```
   breadsmith_marketing/
   ├── src/
   │   ├── config/         # Configuration and constants
   │   ├── core/           # Core functionality
   │   ├── handlers/       # Media and API handlers
   │   ├── models/         # Data models
   │   ├── ui/             # UI components
   │   │   ├── components/ # Reusable UI components
   │   │   └── workers/    # Background workers for UI
   │   └── utils/          # Utility functions
   ├── docs/               # Documentation
   ├── knowledge_base/     # Knowledge base files for AI
   ├── library/            # Media library data
   ├── media_library/      # Media storage
   ├── output/             # Generated output
   ├── run.py              # Main entry point
   ├── run_with_scheduling.py # Entry point with scheduling
   ├── styles.qss          # Application stylesheet
   └── requirements.txt    # Dependencies
   ```

2. **Running Tests**
   ```bash
   pytest tests/
   ```

3. **Code Style**
   - Follow PEP 8 guidelines
   - Use type hints
   - Run `black` for formatting
   - Use `flake8` for linting
   - Use `mypy` for type checking

## Troubleshooting

1. **Common Issues**
   - **Meta API Errors**: Verify credentials and permissions
   - **Media Upload Failures**: Check file size and format
   - **UI Freezes**: Disable auto-refresh for large libraries
   - **Scheduling Issues**: Check system time and date settings

2. **Logs**
   - Check `app_log.log` for detailed error information
   - Log level can be adjusted in `src/config/constants.py`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is proprietary and confidential. Unauthorized copying, distribution, or use is strictly prohibited.

## Support

For support, please contact the development team or create an issue in the repository.