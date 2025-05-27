# 🎬 Veo Video Generation Integration Guide

## Overview

The Crow's Eye platform now includes **Google Veo 3** video generation capabilities, providing high-quality AI-powered video creation directly within the application. This integration allows users to generate professional marketing videos with simple text prompts.

## ✨ Features

### High-Quality Video Generation
- **Multiple Durations**: 5, 10, 15, 30, or 60 seconds
- **Multiple Aspect Ratios**: 16:9 (Landscape), 9:16 (Portrait), 1:1 (Square)
- **Advanced Settings**: Person generation control, quality presets
- **Progress Tracking**: Real-time generation progress with detailed status updates

### Quality Presets
- **Social Media Story**: 9:16 aspect ratio, 15 seconds - Perfect for Instagram/Facebook Stories
- **Social Media Post**: 1:1 aspect ratio, 10 seconds - Square format for social media posts
- **YouTube Short**: 9:16 aspect ratio, 30 seconds - Vertical format for YouTube Shorts
- **Landscape Video**: 16:9 aspect ratio, 30 seconds - Traditional landscape format
- **Quick Preview**: 16:9 aspect ratio, 5 seconds - Quick preview videos
- **Long Form**: 16:9 aspect ratio, 60 seconds - Maximum length videos

### Smart Integration
- **Seamless Workflow**: Generated videos can be automatically loaded into the main application
- **Post Creation**: Direct integration with the post generation workflow
- **File Management**: Automatic file naming with descriptive timestamps
- **Status Monitoring**: Real-time API status checking and error handling

## 🚀 Getting Started

### Prerequisites
1. **Google API Key**: You need a valid `GOOGLE_API_KEY` with access to Veo 3
2. **Environment Setup**: The API key should be set in your environment variables

### Setup Instructions

1. **Set your Google API Key**:
   ```bash
   # Windows (PowerShell)
   $env:GOOGLE_API_KEY="your_api_key_here"
   
   # Windows (Command Prompt)
   set GOOGLE_API_KEY=your_api_key_here
   
   # Linux/Mac
   export GOOGLE_API_KEY="your_api_key_here"
   ```

2. **Or add to .env file**:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```

3. **Launch the Application**:
   ```bash
   python -m src
   ```

## 📖 How to Use

### Accessing Veo Generator

1. **From the Menu Bar**:
   - Go to `Video` → `🎬 Veo Video Generator...`
   - Or use the keyboard shortcut: `Ctrl+V`

2. **The Veo Generator Interface**:
   - **Status Indicator**: Shows if Veo is ready (✅) or has issues (❌)
   - **Prompt Input**: Enter your video description
   - **Quality Presets**: Quick settings for common use cases
   - **Advanced Settings**: Fine-tune duration, aspect ratio, and person generation

### Creating Your First Video

1. **Enter a Prompt**:
   ```
   A serene mountain lake reflecting snow-capped peaks at sunrise
   ```

2. **Choose a Quality Preset**:
   - Select "Social Media Story" for Instagram/Facebook
   - Or "YouTube Short" for vertical content
   - Or "Landscape Video" for traditional format

3. **Adjust Advanced Settings** (Optional):
   - **Duration**: 5-60 seconds
   - **Aspect Ratio**: 16:9, 9:16, or 1:1
   - **Person Generation**: Enable if your prompt includes people

4. **Generate Video**:
   - Click "🎥 Generate Video"
   - Monitor progress in real-time
   - Wait for completion (typically 1-3 minutes)

5. **Use Your Video**:
   - Choose "Yes" to load the video into the main application
   - Or find it in the output directory for manual use

### Example Prompts

#### Nature & Landscapes
- "Ocean waves gently lapping against a sandy beach"
- "A forest path with sunlight filtering through tall trees"
- "Cherry blossoms falling in a peaceful Japanese garden"

#### Food & Lifestyle
- "Steam rising from a freshly baked loaf of bread"
- "Coffee being poured into a white ceramic cup"
- "Fresh ingredients being chopped for a colorful salad"

#### Urban & Architecture
- "A bustling city street with neon lights at night"
- "Modern skyscrapers reaching toward cloudy skies"
- "Rain falling on empty city streets with reflective puddles"

#### Abstract & Artistic
- "Colorful paint mixing and swirling together"
- "Light patterns dancing on a wall"
- "Water droplets creating ripples in slow motion"

## 🔧 Technical Details

### File Output
- **Location**: `output/` directory
- **Naming**: `veo_video_{prompt}_{duration}s_{aspect_ratio}_{timestamp}.mp4`
- **Format**: MP4 video files
- **Quality**: High-definition output from Veo 3

### Performance
- **Generation Time**: 1-5 minutes depending on duration and complexity
- **Timeout**: 15 minutes maximum
- **Progress Updates**: Every 30 seconds during generation
- **Error Handling**: Comprehensive error messages and recovery

### API Usage
- **Model**: `veo-2.0-generate-001` (stable version)
- **Rate Limits**: Managed automatically
- **Retry Logic**: Built-in error recovery
- **Status Monitoring**: Real-time API health checking

## 🛠️ Troubleshooting

### Common Issues

#### ❌ "Veo not ready: Missing GOOGLE_API_KEY"
**Solution**: Set your Google API key in environment variables or .env file

#### ❌ "Client not initialized"
**Solution**: Check your API key validity and internet connection

#### ❌ "Video generation timed out"
**Solution**: Try a shorter duration or simpler prompt

#### ❌ "Invalid duration" or "Invalid aspect ratio"
**Solution**: Use supported values (5-60 seconds, 16:9/9:16/1:1)

### Performance Tips

1. **Start Small**: Begin with 5-10 second videos to test
2. **Clear Prompts**: Use descriptive but concise language
3. **Avoid Complexity**: Simpler scenes generate faster and more reliably
4. **Check Status**: Ensure the green ✅ status before generating

### Best Practices

1. **Prompt Writing**:
   - Be specific but not overly complex
   - Include lighting, mood, and style preferences
   - Avoid copyrighted content or specific people

2. **Quality Settings**:
   - Use presets for consistent results
   - Match aspect ratio to your target platform
   - Consider your audience when choosing duration

3. **Workflow Integration**:
   - Generate videos first, then create posts
   - Use the auto-load feature for seamless workflow
   - Keep generated videos organized in the output folder

## 🔄 Integration with Main App

### Automatic Loading
When a video is successfully generated, you can:
1. **Load Immediately**: Choose "Yes" to load into the main application
2. **Manual Loading**: Use the media selector to choose the video later
3. **Post Creation**: Generate captions and posts using the video

### File Management
- Videos are saved with descriptive names
- Timestamps prevent filename conflicts
- Output directory is automatically created
- Files are ready for immediate use

## 📊 Quality Comparison

| Preset | Aspect Ratio | Duration | Best For |
|--------|-------------|----------|----------|
| Social Media Story | 9:16 | 15s | Instagram/Facebook Stories |
| Social Media Post | 1:1 | 10s | General social media posts |
| YouTube Short | 9:16 | 30s | YouTube Shorts, TikTok |
| Landscape Video | 16:9 | 30s | YouTube, website headers |
| Quick Preview | 16:9 | 5s | Product previews, teasers |
| Long Form | 16:9 | 60s | Detailed demonstrations |

## 🎯 Use Cases

### Marketing Videos
- Product demonstrations
- Brand storytelling
- Seasonal campaigns
- Event promotions

### Social Media Content
- Instagram Stories and Reels
- YouTube Shorts
- TikTok videos
- Facebook posts

### Website Content
- Hero section videos
- Background animations
- Product showcases
- About us videos

## 🔮 Future Enhancements

### Planned Features
- **Image-to-Video**: Generate videos from uploaded images
- **Style Presets**: Cinematic, commercial, artistic styles
- **Batch Generation**: Multiple videos from prompt variations
- **Custom Templates**: Save and reuse prompt templates

### Advanced Options
- **Negative Prompts**: Specify what to avoid
- **Style Transfer**: Apply specific visual styles
- **Motion Control**: Control camera movement and pacing
- **Audio Integration**: Automatic background music

## 📞 Support

### Getting Help
- **Status Check**: Always check the green ✅ status first
- **Error Messages**: Read error messages carefully for specific solutions
- **API Limits**: Monitor your Google API usage
- **Community**: Share prompts and tips with other users

### Reporting Issues
When reporting issues, include:
1. Your prompt text
2. Selected settings (duration, aspect ratio)
3. Error message (if any)
4. API key status (without revealing the key)

---

**Happy Video Creating! 🎬✨**

The Veo integration brings professional video generation capabilities directly to your marketing workflow. Experiment with different prompts and settings to discover what works best for your content strategy. 