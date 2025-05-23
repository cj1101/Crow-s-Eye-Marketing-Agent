# Crow's Eye Marketing Feature - Test Instructions

## Overview
Crow's Eye is a smart marketing automation feature that has been integrated into the Breadsmith Marketing Tool. It provides advanced tools for organizing media content and generating optimized galleries and captions for social media posts.

## Features

### Media Organization
- Automatic categorization of media files into Raw Photos, Raw Videos, and Post-Ready content
- Media search capabilities using natural language
- Visual thumbnails and selection interface

### Smart Gallery Generator
- AI-powered selection of media items based on natural language prompts
- Support for prompts like "pick the best 5 for a winter campaign"
- Automatic photo enhancement option

### Caption Generation
- Generate captions based on selected media
- Control tone using natural language prompts (e.g., "professional", "casual", "funny")
- Hashtag suggestions included automatically

## Testing Instructions

### Step 1: Launch the Application
1. Run the application using the usual method (either `run.py` or `run_app.bat`)
2. The application should start with the default Caption Generator tab active

### Step 2: Switch to Crow's Eye Tab
1. Click on the "Crow's Eye Marketing" tab button in the top tab bar
2. The interface should switch to the Crow's Eye features

### Step 3: Test Media Library
1. Check that your media files are displayed in the appropriate tabs (Raw Photos, Raw Videos, Post-Ready)
2. Try the search function by entering keywords in the search box
3. Test the media item selection by clicking on thumbnails or checkboxes

### Step 4: Test Gallery Generation
1. Select multiple media items by clicking on them
2. Enter a prompt in the "Natural Language Prompt" field (e.g., "Select the best 3 images for a summer campaign")
3. Click "Generate Gallery"
4. Verify that a selection of media appears in the "Generated Gallery" section

### Step 5: Test Caption Generation
1. With a gallery generated, enter a tone prompt (e.g., "Professional and concise")
2. Click "Generate Caption"
3. Verify that a caption appears in the text area below

### Step 6: Test Gallery Saving
1. Enter a name for your gallery in the input field
2. Click "Save Gallery"
3. Verify that a success message appears
4. Check that the gallery was saved in the `media_gallery` directory as a JSON file

## Troubleshooting

If you encounter any issues:

1. Check the application logs for error messages
2. Ensure that all required directories exist
3. Verify that your media files are in the expected format and location

## Notes

- This feature is designed to work with the existing media library
- No external API keys are required for the basic functionality
- In this version, AI functionality is simulated - in a production version, it would connect to actual AI services

For any issues or feedback, please contact the development team. 