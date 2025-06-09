import asyncio
import base64
import io
from typing import List, Optional, Dict, Any
from datetime import datetime

import openai
import google.generativeai as genai
from PIL import Image

from crow_eye_api.core.config import settings


class AIService:
    """Service for AI-powered content generation and analysis."""
    
    def __init__(self):
        """Initialize AI clients."""
        # OpenAI setup
        if settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
        
        # Google AI setup
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.gemini_model = None
    
    async def generate_caption(
        self, 
        image_content: bytes,
        style: str = "engaging",
        platform: str = "general"
    ) -> str:
        """
        Generate AI caption for an image.
        
        Args:
            image_content: Image file content as bytes
            style: Caption style (engaging, professional, casual, creative)
            platform: Target platform (instagram, facebook, twitter, general)
            
        Returns:
            Generated caption text
        """
        # Prepare style and platform prompts
        style_prompts = {
            "engaging": "Create an engaging and compelling caption that would get lots of engagement",
            "professional": "Create a professional and polished caption suitable for business use",
            "casual": "Create a casual and friendly caption with a conversational tone",
            "creative": "Create a creative and artistic caption with unique perspective"
        }
        
        platform_prompts = {
            "instagram": "optimized for Instagram with relevant hashtags",
            "facebook": "optimized for Facebook with community engagement focus",
            "twitter": "optimized for Twitter, concise and impactful",
            "linkedin": "optimized for LinkedIn, professional networking focus",
            "general": "suitable for multiple social media platforms"
        }
        
        style_instruction = style_prompts.get(style, style_prompts["engaging"])
        platform_instruction = platform_prompts.get(platform, platform_prompts["general"])
        
        # Try Gemini first if available
        if self.gemini_model:
            try:
                return await self._generate_caption_gemini(
                    image_content, style_instruction, platform_instruction
                )
            except Exception as e:
                print(f"Gemini caption generation failed: {e}")
        
        # Fallback to OpenAI
        if settings.OPENAI_API_KEY:
            try:
                return await self._generate_caption_openai(
                    image_content, style_instruction, platform_instruction
                )
            except Exception as e:
                print(f"OpenAI caption generation failed: {e}")
        
        # Fallback to basic caption
        return self._generate_basic_caption(style, platform)
    
    async def _generate_caption_gemini(
        self, 
        image_content: bytes, 
        style_instruction: str, 
        platform_instruction: str
    ) -> str:
        """Generate caption using Google Gemini."""
        # Convert image for Gemini
        image = Image.open(io.BytesIO(image_content))
        
        prompt = f"""
        Analyze this image and {style_instruction} that is {platform_instruction}.
        
        Guidelines:
        - Keep it engaging and authentic
        - Include relevant emojis if appropriate for the platform
        - For Instagram: include 3-5 relevant hashtags at the end
        - For Twitter: keep under 280 characters
        - Focus on what makes this image special or interesting
        - Don't mention technical details about the image file
        
        Caption:
        """
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: self.gemini_model.generate_content([prompt, image])
        )
        
        return response.text.strip()
    
    async def _generate_caption_openai(
        self, 
        image_content: bytes, 
        style_instruction: str, 
        platform_instruction: str
    ) -> str:
        """Generate caption using OpenAI GPT-4 Vision."""
        # Encode image to base64
        base64_image = base64.b64encode(image_content).decode('utf-8')
        
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""
                        Analyze this image and {style_instruction} that is {platform_instruction}.
                        
                        Guidelines:
                        - Keep it engaging and authentic
                        - Include relevant emojis if appropriate for the platform
                        - For Instagram: include 3-5 relevant hashtags at the end
                        - For Twitter: keep under 280 characters
                        - Focus on what makes this image special or interesting
                        - Don't mention technical details about the image file
                        
                        Caption:
                        """
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: openai.ChatCompletion.create(
                model="gpt-4-vision-preview",
                messages=messages,
                max_tokens=300
            )
        )
        
        return response.choices[0].message.content.strip()
    
    def _generate_basic_caption(self, style: str, platform: str) -> str:
        """Generate a basic caption when AI services are unavailable."""
        basic_captions = {
            "engaging": "✨ Sharing a moment that caught my eye! What do you think?",
            "professional": "Sharing quality content with our community.",
            "casual": "Just wanted to share this with you all! 😊",
            "creative": "Sometimes the best moments are the unexpected ones ✨"
        }
        
        caption = basic_captions.get(style, basic_captions["engaging"])
        
        if platform == "instagram":
            caption += " #photography #moment #share"
        
        return caption
    
    async def generate_tags(
        self, 
        image_content: bytes, 
        max_tags: int = 10
    ) -> List[str]:
        """
        Generate AI tags for an image.
        
        Args:
            image_content: Image file content as bytes
            max_tags: Maximum number of tags to generate
            
        Returns:
            List of generated tags
        """
        # Try Gemini first
        if self.gemini_model:
            try:
                return await self._generate_tags_gemini(image_content, max_tags)
            except Exception as e:
                print(f"Gemini tag generation failed: {e}")
        
        # Fallback to basic tags
        return ["photo", "image", "content", "social"]
    
    async def _generate_tags_gemini(self, image_content: bytes, max_tags: int) -> List[str]:
        """Generate tags using Google Gemini."""
        image = Image.open(io.BytesIO(image_content))
        
        prompt = f"""
        Analyze this image and generate {max_tags} relevant tags or keywords that describe:
        - Main subjects or objects in the image
        - Colors, mood, or atmosphere
        - Activities or actions happening
        - Style or aesthetic
        - Potential use cases or contexts
        
        Return only the tags as a comma-separated list, no other text.
        Example format: nature, sunset, peaceful, orange, landscape, photography
        """
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: self.gemini_model.generate_content([prompt, image])
        )
        
        tags_text = response.text.strip()
        tags = [tag.strip() for tag in tags_text.split(',')]
        return tags[:max_tags]
    
    async def analyze_content_for_highlights(
        self, 
        caption: str, 
        tags: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze content to suggest highlights and improvements.
        
        Args:
            caption: Current caption text
            tags: List of current tags
            
        Returns:
            Dictionary with analysis and suggestions
        """
        if not settings.OPENAI_API_KEY and not settings.GEMINI_API_KEY:
            return {
                "highlights": ["Quality content", "Engaging post"],
                "suggestions": ["Consider adding more descriptive details"],
                "engagement_score": 7,
                "improvements": []
            }
        
        prompt = f"""
        Analyze this social media content and provide insights:
        
        Caption: "{caption}"
        Tags: {', '.join(tags)}
        
        Please provide a JSON response with:
        1. "highlights" - 2-3 positive aspects of this content
        2. "suggestions" - 2-3 actionable suggestions to improve engagement
        3. "engagement_score" - predicted engagement score from 1-10
        4. "improvements" - specific areas that could be enhanced
        
        Focus on content quality, engagement potential, and social media best practices.
        """
        
        try:
            if self.gemini_model:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None, 
                    lambda: self.gemini_model.generate_content(prompt)
                )
                result_text = response.text.strip()
            elif settings.OPENAI_API_KEY:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: openai.ChatCompletion.create(
                        model="gpt-4",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=300
                    )
                )
                result_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            import json
            try:
                return json.loads(result_text)
            except json.JSONDecodeError:
                # Fallback if AI doesn't return valid JSON
                return {
                    "highlights": ["Authentic content", "Good visual appeal"],
                    "suggestions": ["Consider adding call-to-action", "Use trending hashtags"],
                    "engagement_score": 8,
                    "improvements": ["Enhance caption storytelling"]
                }
                
        except Exception as e:
            print(f"Content analysis failed: {e}")
            return {
                "highlights": ["Quality content shared"],
                "suggestions": ["Continue creating engaging posts"],
                "engagement_score": 7,
                "improvements": ["Keep experimenting with content styles"]
            }


# Global instance
ai_service = AIService() 