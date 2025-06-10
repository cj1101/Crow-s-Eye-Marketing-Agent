# Segment-Based Highlight Reel Generation

## Overview

The segment-based highlight reel feature allows users to select a time range from their video as an example of what they want to find more of. This makes highlight generation much more efficient and accurate than trying to identify actions from scratch.

## How It Works

### Traditional Approach (Before)
1. User provides a text prompt like "throwing pokeballs"
2. System analyzes entire video looking for pokeball throwing actions
3. Takes a long time to identify specific actions
4. Results may be inconsistent

### New Segment-Based Approach
1. User selects a **time segment** from their video (e.g., 45.2s to 48.7s) that represents what they want
2. System analyzes that specific segment intensely using AI
3. System finds all similar instances throughout the video
4. Context padding is added before each highlight scene
5. Best segments are selected to fit target duration
6. Price optimization ensures cost-effective analysis

## API Usage

### Schema Changes

New `HighlightExample` schema:
```json
{
  "start_time": 45.2,                          // Required - start of example segment
  "end_time": 48.7,                           // Required - end of example segment
  "description": "Person throwing a pokeball"  // Optional - what makes this segment special
}
```

Updated `HighlightGenerate` schema:
```json
{
  "media_ids": [123],
  "duration": 30,
  "highlight_type": "story",
  "style": "dynamic",
  "include_text": true,
  "include_music": false,
  "example": {                                 // NEW FIELD
    "start_time": 45.2,
    "end_time": 48.7,
    "description": "The pokeball throwing motion I want to find more of"
  },
  "context_padding": 2.0,                      // NEW FIELD - seconds of context before each scene
  "content_instructions": "Focus on mobile gaming actions with clear hand movements"  // NEW FIELD
}
```

### API Endpoint

```http
POST /api/v1/ai/highlights/generate
Content-Type: application/json

{
  "media_ids": [123],
  "duration": 30,
  "example": {
    "start_time": 45.2,
    "end_time": 48.7,
    "description": "The pokeball throwing motion I want to find more of"
  },
  "context_padding": 3.0,
  "content_instructions": "Focus on mobile gaming with clear throwing gestures"
}
```

## Example Usage Scenarios

### Scenario 1: Short Action Segment
```json
{
  "media_ids": [123],
  "duration": 30,
  "example": {
    "start_time": 45.2,
    "end_time": 47.8,
    "description": "Quick pokeball throwing motion"
  },
  "context_padding": 2.0,
  "content_instructions": "Focus on the hand gesture and timing"
}
```

### Scenario 2: Longer Context Segment
```json
{
  "media_ids": [123],
  "duration": 60,
  "example": {
    "start_time": 120.5,
    "end_time": 135.0,
    "description": "Full Pokemon Go encounter sequence including targeting and throwing"
  },
  "context_padding": 3.0,
  "content_instructions": "Include the complete interaction flow"
}
```

### Scenario 3: Minimal Description
```json
{
  "media_ids": [123],
  "duration": 30,
  "example": {
    "start_time": 78.1,
    "end_time": 80.5
  },
  "context_padding": 1.5,
  "content_instructions": "Find similar fast-paced gaming moments"
}
```

## Technical Implementation

### Core Components

1. **Example Analysis**: The system analyzes the provided example intensely using AI to understand:
   - Visual elements (colors, shapes, objects, textures)
   - Actions and movements
   - Context and setting
   - People and their positioning
   - Objects and tools
   - Visual style and mood

2. **Frame Sampling**: The video is sampled at regular intervals (every 0.5-2 seconds depending on video length)

3. **Similarity Matching**: Each frame is compared to the example using AI analysis with similarity scoring (0-10 scale)

4. **Segment Grouping**: Similar frames within 3 seconds of each other are grouped into continuous segments

5. **Context Padding**: Each segment is extended with user-specified context padding (default 2 seconds before the action)

6. **Selection**: Best segments are selected based on similarity scores to fit the target duration

### Performance Optimizations

- **Intelligent Sampling**: Longer videos are sampled less frequently to balance accuracy with processing time
- **Threshold Filtering**: Only frames with similarity scores > 0.5 are considered
- **Batch Processing**: Frames are analyzed in batches with progress logging
- **Efficient Cleanup**: Temporary files are properly cleaned up after analysis

## Benefits

### For Users
- **Much Faster**: No need to wait for the system to figure out what action you want
- **More Accurate**: Direct comparison to your example ensures better results
- **Flexible Input**: Can use images, descriptions, or timestamps as examples
- **Context Control**: Adjustable context padding to get the right amount of lead-in

### For Developers
- **Reusable**: The similarity matching system can be extended for other use cases
- **Scalable**: Efficient sampling and processing for videos of various lengths
- **Maintainable**: Clear separation of concerns with dedicated methods for each step

## Configuration Options

### Context Padding
- **Default**: 2.0 seconds
- **Range**: 0.0 - 10.0 seconds
- **Purpose**: Adds context before each highlight scene so viewers understand what's happening

### Similarity Threshold
- **Default**: 0.5 (50% similarity)
- **Range**: 0.0 - 1.0
- **Purpose**: Minimum similarity score required for a frame to be considered a match

### Sampling Interval
- **Automatic**: Based on video duration (0.5-2 seconds)
- **Purpose**: Balance between accuracy and processing time

## Error Handling

The system includes comprehensive error handling:

- **Invalid Example Data**: Returns clear error messages if example data is malformed
- **Missing Video**: Validates video file exists before processing
- **AI Analysis Failures**: Graceful fallback to motion-based analysis if AI fails
- **No Similar Frames**: Returns informative message if no similar content is found
- **File Cleanup**: Ensures temporary files are cleaned up even if errors occur

## Future Enhancements

Potential improvements for future versions:

1. **Multiple Examples**: Support for providing multiple example images
2. **Negative Examples**: Specify what NOT to include
3. **Temporal Patterns**: Detect sequences of actions, not just individual moments
4. **Visual Similarity**: Use computer vision for faster similarity detection
5. **Learning**: Improve similarity detection based on user feedback

## Testing

Use the provided test script to verify the implementation:

```bash
python test_example_highlights.py
```

This will verify that all methods are properly implemented and the API is ready to use.

## Migration Guide

### From Traditional Highlights
If you're currently using the traditional highlight generation:

**Before:**
```json
{
  "media_ids": [123],
  "duration": 30,
  "prompt": "throwing pokeballs"
}
```

**After:**
```json
{
  "media_ids": [123],
  "duration": 30,
  "example": {
    "start_time": 45.2,
    "end_time": 48.7,
    "description": "The pokeball throwing motion I want to find more of"
  },
  "context_padding": 2.0,
  "content_instructions": "Focus on mobile gaming actions with clear hand movements"
}
```

The traditional method is still available as a fallback when no example segment is provided. 