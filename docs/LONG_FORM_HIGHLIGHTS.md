# Long-Form Highlight Generation

Transform 1-3 hours of content into professional 2-5 minute highlight reels with cost-optimized AI analysis.

## 🎯 Overview

The Long-Form Highlight Generator uses a multi-stage approach to create engaging highlight reels from extended content while keeping AI costs minimal:

- **Technical Pre-filtering**: Motion and audio analysis (FREE)
- **Intelligent AI Sampling**: Only 5-20 strategic AI calls per video
- **Smart Assembly**: Professional editing with transitions

## 💰 Cost Structure

| Video Length | AI Calls | Estimated Cost | Processing Time |
|-------------|----------|----------------|-----------------|
| 1 hour      | 5-10     | $0.05-$0.15   | 5-8 minutes    |
| 2 hours     | 10-15    | $0.15-$0.25   | 8-12 minutes   |
| 3 hours     | 15-20    | $0.20-$0.35   | 12-18 minutes  |

**Cost Savings**: 90% reduction compared to naive frame-by-frame analysis

## 🚀 API Usage

### 1. Cost Estimation (Recommended First Step)

```bash
POST /api/highlights/long-form/estimate
Content-Type: application/json

{
  "video_path": "/path/to/your/video.mp4",
  "cost_optimize": true
}
```

**Response:**
```json
{
  "duration_hours": 2.5,
  "estimated_ai_calls": 15,
  "estimated_cost_usd": 0.25,
  "processing_time_minutes": "10-15",
  "recommendations": [
    "Consider using cost optimization for videos longer than 2 hours",
    "Estimated savings with optimization: $0.18"
  ]
}
```

### 2. Generate Long-Form Highlight Reel

```bash
POST /api/highlights/long-form
Content-Type: application/json

{
  "video_path": "/path/to/your/video.mp4",
  "duration": 180,
  "prompt": "focus on exciting moments, audience reactions, and key highlights",
  "cost_optimize": true,
  "style": "cinematic"
}
```

**Response:**
```json
{
  "id": "highlight_abc123",
  "media_ids": ["/path/to/your/video.mp4"],
  "duration": 180,
  "style": "cinematic", 
  "music_style": "cinematic",
  "text_overlay": "Generated from 2.5h content",
  "created_at": "2024-01-15T10:30:00Z",
  "status": "completed",
  "preview_url": "/highlights/highlight_abc123/preview",
  "download_url": "/data/output/video_longform_highlight_20240115_103000.mp4",
  "progress": 100
}
```

## 🎬 Example Use Cases

### Gaming Stream Highlights
```json
{
  "video_path": "/streams/gaming_session_3h.mp4",
  "duration": 240,
  "prompt": "best plays, funny moments, epic wins, chat reactions",
  "cost_optimize": true
}
```

### Conference Talk Summary
```json
{
  "video_path": "/talks/conference_presentation_90min.mp4", 
  "duration": 120,
  "prompt": "key points, audience questions, demonstrations, important slides",
  "cost_optimize": true
}
```

### Event Coverage
```json
{
  "video_path": "/events/wedding_ceremony_2h.mp4",
  "duration": 300,
  "prompt": "emotional moments, speeches, celebrations, key ceremonies",
  "cost_optimize": true
}
```

## ⚙️ Technical Features

### Multi-Stage Processing

1. **Technical Analysis (Free)**
   - Motion detection using frame variance
   - Audio activity analysis (RMS levels)
   - Scene change detection
   - Removes 60-80% of boring content

2. **AI Analysis (Cost-Optimized)**
   - Strategic frame sampling (1 per 5-10 minutes)
   - Prompt-aware relevance scoring
   - Capped at maximum 20 AI calls regardless of video length

3. **Professional Assembly**
   - Smooth fade transitions
   - Optimal segment selection
   - Higher quality encoding
   - Chapter markers (optional)

### Cost Optimization

- **Enabled (Default)**: 5-20 AI calls maximum
- **Disabled**: 30 calls per hour (use only for critical content)

The system automatically balances quality vs cost using technical pre-filtering.

## 🔧 Requirements

- **Minimum Video Length**: 30 minutes
- **Maximum Video Length**: 4 hours  
- **Supported Formats**: MP4, MOV, AVI, MKV
- **Required Tier**: Creator+ ($9/month and above)

## 📊 Quality vs Cost Trade-offs

| Setting | Quality | Cost | Use Case |
|---------|---------|------|----------|
| `cost_optimize: true` | ⭐⭐⭐⭐ | 💰 | Most content, regular use |
| `cost_optimize: false` | ⭐⭐⭐⭐⭐ | 💰💰💰 | Critical/premium content only |

## 🎨 Output Styles

- **`cinematic`**: Professional transitions, higher quality
- **`documentary`**: Clean cuts, informative style  
- **`energetic`**: Fast-paced, dynamic transitions

## 🚨 Best Practices

1. **Always estimate costs first** using the `/estimate` endpoint
2. **Start with shorter videos** (30-60 minutes) to test the system
3. **Use descriptive prompts** for better AI analysis
4. **Enable cost optimization** unless content is extremely important
5. **Process during off-peak hours** for faster results

## 🔍 Monitoring & Analytics

Each processing job logs:
- Total AI calls made
- Actual cost incurred  
- Processing time
- Quality metrics
- User satisfaction feedback

## 🆘 Troubleshooting

### Common Issues

**"Video is too long (>4 hours)"**
- Split your video into shorter segments
- Consider using multiple highlight reels

**"AI handler not available"**
- Ensure Gemini API key is configured
- Check internet connectivity
- Verify dependencies are installed

**"High cost detected"**
- Consider enabling cost optimization
- Use shorter target duration
- Split long videos into segments

### Support

For issues or questions:
1. Check the logs in `app_log.log`
2. Test with shorter videos first
3. Contact support with error details

## 🚧 Future Enhancements

- **Batch processing** for multiple videos
- **Custom AI prompts** for specific content types
- **Advanced chapter markers** with titles
- **Music synchronization** for highlights
- **Social media format optimization**

---

*Last updated: January 2024*
*Feature Status: ✅ Production Ready* 