"""
AI Content Service for Crow's Eye API.
Handles AI-powered content generation including captions, hashtags, and suggestions.
"""

import asyncio
from typing import Dict, Any, List, Optional
import logging


class AIContentService:
    """Service for AI-powered content generation."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
    async def generate_post_content(
        self,
        post,
        regenerate_caption: bool = True,
        regenerate_instructions: bool = False,
        keep_existing: bool = False
    ) -> Dict[str, Any]:
        """
        Generate AI content for a post.
        
        Args:
            post: Post object to generate content for
            regenerate_caption: Whether to regenerate the caption
            regenerate_instructions: Whether to regenerate custom instructions
            keep_existing: Whether to keep existing content and add to it
            
        Returns:
            Dictionary with updated content
        """
        try:
            updated_content = {}
            
            if regenerate_caption:
                # Generate new caption based on media and existing content
                new_caption = await self._generate_caption_for_post(post)
                
                if keep_existing and post.caption:
                    updated_content["caption"] = f"{post.caption}\n\n{new_caption}"
                else:
                    updated_content["caption"] = new_caption
            
            if regenerate_instructions:
                # Generate new custom instructions
                new_instructions = await self._generate_instructions_for_post(post)
                
                if keep_existing and post.custom_instructions:
                    updated_content["custom_instructions"] = f"{post.custom_instructions}\n\n{new_instructions}"
                else:
                    updated_content["custom_instructions"] = new_instructions
            
            return updated_content
            
        except Exception as e:
            self.logger.error(f"Error generating post content: {e}")
            return {}
    
    async def _generate_caption_for_post(self, post) -> str:
        """Generate a caption for a specific post."""
        try:
            # Determine the style based on platforms
            style = "engaging"
            if "linkedin" in post.platforms:
                style = "professional"
            elif "tiktok" in post.platforms:
                style = "creative"
            
            # Use the primary platform for optimization
            primary_platform = post.platforms[0] if post.platforms else "general"
            
            # For now, generate a basic caption
            # In a full implementation, this would use the media content
            caption_templates = {
                "instagram": "✨ Sharing something special with you today! What do you think? 📸 #content #instagram #share",
                "facebook": "Excited to share this with our community! Let us know your thoughts in the comments below.",
                "tiktok": "POV: When you create something amazing 🔥 #fyp #viral #content",
                "linkedin": "Sharing insights from our latest project. What are your thoughts on this approach?",
                "youtube": "Check out this amazing content! Don't forget to like and subscribe for more.",
                "pinterest": "Beautiful inspiration for your next project! Save this for later 📌"
            }
            
            base_caption = caption_templates.get(primary_platform, caption_templates["instagram"])
            
            # Add platform-specific hashtags
            if primary_platform == "instagram":
                base_caption += " #photography #creative #inspiration"
            elif primary_platform == "tiktok":
                base_caption += " #trending #viral #foryou"
            elif primary_platform == "linkedin":
                base_caption += " #business #professional #insights"
            
            return base_caption
            
        except Exception as e:
            self.logger.error(f"Error generating caption: {e}")
            return "Check out this amazing content! 🌟"
    
    async def _generate_instructions_for_post(self, post) -> str:
        """Generate custom instructions for a post."""
        try:
            platform_instructions = {
                "instagram": "Optimize for Instagram engagement with relevant hashtags and visual appeal",
                "facebook": "Focus on community engagement and encourage comments and shares",
                "tiktok": "Create viral-worthy content with trending sounds and effects",
                "linkedin": "Maintain professional tone while being engaging and informative",
                "youtube": "Optimize for YouTube algorithm with compelling thumbnails and descriptions",
                "pinterest": "Create pin-worthy content that drives traffic and saves"
            }
            
            instructions = []
            for platform in post.platforms:
                if platform in platform_instructions:
                    instructions.append(f"For {platform}: {platform_instructions[platform]}")
            
            return ". ".join(instructions) if instructions else "Optimize content for maximum engagement across all platforms"
            
        except Exception as e:
            self.logger.error(f"Error generating instructions: {e}")
            return "Create engaging content optimized for your target audience"
    
    async def generate_hashtags(
        self,
        content: str,
        platforms: List[str],
        niche: str,
        count: int = 10
    ) -> List[str]:
        """Generate relevant hashtags for content."""
        try:
            # Basic hashtag generation based on content and niche
            base_hashtags = {
                "general": ["#content", "#social", "#share", "#community", "#engagement"],
                "business": ["#business", "#entrepreneur", "#success", "#growth", "#innovation"],
                "lifestyle": ["#lifestyle", "#inspiration", "#motivation", "#wellness", "#life"],
                "tech": ["#technology", "#innovation", "#digital", "#tech", "#future"],
                "fitness": ["#fitness", "#health", "#workout", "#wellness", "#motivation"],
                "food": ["#food", "#foodie", "#delicious", "#cooking", "#recipe"],
                "travel": ["#travel", "#adventure", "#explore", "#wanderlust", "#vacation"],
                "fashion": ["#fashion", "#style", "#outfit", "#trendy", "#ootd"]
            }
            
            hashtags = base_hashtags.get(niche.lower(), base_hashtags["general"]).copy()
            
            # Add platform-specific hashtags
            for platform in platforms:
                if platform == "instagram":
                    hashtags.extend(["#instagood", "#photooftheday", "#instadaily"])
                elif platform == "tiktok":
                    hashtags.extend(["#fyp", "#viral", "#trending"])
                elif platform == "linkedin":
                    hashtags.extend(["#professional", "#networking", "#career"])
            
            # Remove duplicates and limit to requested count
            unique_hashtags = list(set(hashtags))
            return unique_hashtags[:count]
            
        except Exception as e:
            self.logger.error(f"Error generating hashtags: {e}")
            return ["#content", "#social", "#share"]
    
    async def generate_content_suggestions(
        self,
        media_id: str,
        platforms: List[str],
        content_type: str = "caption",
        variations: int = 3
    ) -> List[Dict[str, Any]]:
        """Generate content suggestions for media."""
        try:
            suggestions = []
            
            for i in range(variations):
                if content_type == "caption":
                    suggestion = {
                        "type": "caption",
                        "content": await self._generate_variation_caption(platforms, i),
                        "tone": ["professional", "casual", "creative"][i % 3],
                        "platforms": platforms
                    }
                elif content_type == "story":
                    suggestion = {
                        "type": "story",
                        "content": await self._generate_story_content(platforms, i),
                        "duration": "15s",
                        "platforms": platforms
                    }
                else:
                    suggestion = {
                        "type": "description",
                        "content": await self._generate_description_content(platforms, i),
                        "length": "medium",
                        "platforms": platforms
                    }
                
                suggestions.append(suggestion)
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error generating content suggestions: {e}")
            return []
    
    async def _generate_variation_caption(self, platforms: List[str], variation: int) -> str:
        """Generate caption variations."""
        variations = [
            "🌟 Excited to share this with you! What are your thoughts?",
            "✨ Something special coming your way! Let me know what you think in the comments.",
            "🔥 This is exactly what we needed today! Who else agrees?"
        ]
        return variations[variation % len(variations)]
    
    async def _generate_story_content(self, platforms: List[str], variation: int) -> str:
        """Generate story content."""
        stories = [
            "Behind the scenes of creating this amazing content!",
            "Quick tip: This is how we make our content stand out!",
            "Swipe up to see the full process!"
        ]
        return stories[variation % len(stories)]
    
    async def _generate_description_content(self, platforms: List[str], variation: int) -> str:
        """Generate description content."""
        descriptions = [
            "Dive deep into this comprehensive guide that covers everything you need to know about creating engaging content.",
            "A detailed look at the process behind creating content that resonates with your audience.",
            "Explore the techniques and strategies that make content truly impactful and memorable."
        ]
        return descriptions[variation % len(descriptions)]


# Create service instance
ai_content_service = AIContentService() 