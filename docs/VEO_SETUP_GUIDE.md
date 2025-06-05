# 🎬 Veo 3 Setup Guide

This guide will help you set up Veo 3 video generation in your social media tool.

## 📋 Prerequisites

1. **Google Cloud Account** with billing enabled
2. **Google API Key** with access to Gemini API
3. **Python 3.8+** with pip

## 🚀 Quick Setup

### Step 1: Install Dependencies

```bash
pip install google-genai>=1.10.0
```

### Step 2: Set Up API Key

1. Get your Google API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Set it as an environment variable:

**Windows:**
```cmd
set GOOGLE_API_KEY=your_api_key_here
```

**Linux/Mac:**
```bash
export GOOGLE_API_KEY=your_api_key_here
```

**Or create a `.env` file:**
```
GOOGLE_API_KEY=your_api_key_here
```

### Step 3: Test Basic Setup

Run the basic test:
```bash
cd src/api/ai
python veo_simple_test.py
```

You should see:
```
✅ API key found
✅ Google Gen AI library imported successfully
✅ Gen AI client created successfully
🎉 Basic Veo setup test passed!
```

### Step 4: Test Video Generation

Run the generation test:
```bash
python veo_generate_test.py
```

This will generate a simple test video (takes 2-3 minutes).

### Step 5: Test UI Integration

Run the test app:
```bash
python test_veo_app.py
```

## 🧪 Testing Files Created

- `src/api/ai/veo_simple_test.py` - Basic setup test
- `src/api/ai/veo_generate_test.py` - Video generation test
- `src/api/ai/veo_simple.py` - Simple wrapper class
- `src/components/simple_veo_widget.py` - Basic UI widget
- `test_veo_app.py` - Standalone test app

## 🔧 Troubleshooting

### "No GOOGLE_API_KEY found"
- Make sure your API key is set in environment variables
- Check that the key has access to Gemini API

### "Failed to import google.genai"
- Install the library: `pip install google-genai>=1.10.0`
- Make sure you're using Python 3.8+

### "Video generation timed out"
- This is normal during peak hours
- Try again later or increase timeout in the code

### "No video was generated"
- Check your API quota and billing
- Verify your prompt doesn't violate content policies

## 📈 Next Steps

Once basic testing works:

1. **Integrate with main app** - Add the SimpleVeoWidget to your main interface
2. **Expand functionality** - Add more options (aspect ratios, durations, etc.)
3. **Add platform optimization** - Generate videos optimized for different social platforms
4. **Implement iterative editing** - Allow users to refine videos based on feedback

## 💰 Cost Considerations

- Veo is a **paid feature** (not available in free tier)
- Each video generation costs credits
- Consider implementing usage limits for users
- Monitor costs in Google Cloud Console

## 🔗 Useful Links

- [Veo Documentation](https://ai.google.dev/gemini-api/docs/video)
- [Google AI Studio](https://aistudio.google.com/)
- [Pricing Information](https://ai.google.dev/pricing)
- [API Reference](https://ai.google.dev/api) 