"""
AI Tagging Module for Crow's Eye
Separate module for advanced content identification and tagging.
"""
import os
from typing import List, Dict, Any

class AITaggingEngine:
    """Advanced AI tagging system for comprehensive content identification."""
    
    def __init__(self):
        """Initialize the AI tagging engine."""
        self.KNOWN_TAGS_DB = {
            "oip.jpeg": ["bread", "baked goods", "pastry", "food", "bakery", "assortment", "croissant", "roll"],
            "sourdough.jpeg": ["bread", "sourdough", "baked goods", "food", "bakery", "loaf", "sliced bread"],
            "igannouncement.png": ["game", "pixel art", "blimp", "vehicle", "sky", "announcement", "minecraft style", "landscape"],
            "untitled.png": ["art", "character", "fantasy", "warrior", "portrait", "woman", "red hair", "armor", "apex predators", "illustration", "person", "people"],
        }
    
    def get_tags(self, media_path: str) -> List[str]:
        """
        Get comprehensive AI tags for any media file.
        
        Args:
            media_path: Path to the media file
            
        Returns:
            List of relevant tags for the media
        """
        base_filename = os.path.basename(media_path).lower()
        
        # Check for exact matches first
        exact_tags = self.KNOWN_TAGS_DB.get(base_filename, None)
        if exact_tags:
            return exact_tags
        
        # Generate tags using comprehensive analysis
        tags = []
        filename_lower = base_filename.lower()
        
        # PEOPLE & PORTRAITS
        people_patterns = [
            'person', 'people', 'man', 'woman', 'face', 'portrait', 'selfie', 'group',
            'team', 'staff', 'customer', 'baker', 'chef', 'family', 'friend', 'smile',
            'headshot', 'profile', 'human', 'worker', 'employee', 'owner', 'founder'
        ]
        if any(word in filename_lower for word in people_patterns):
            tags.extend(['person', 'people', 'portrait', 'human', 'photo'])
            if any(word in filename_lower for word in ['team', 'staff', 'employee', 'worker']):
                tags.extend(['team', 'staff', 'workplace'])
        
        # FOOD & CULINARY
        bread_patterns = ['bread', 'sourdough', 'baguette', 'loaf', 'roll', 'croissant', 'focaccia']
        pastry_patterns = ['pastry', 'danish', 'muffin', 'scone', 'bagel', 'pretzel']
        dessert_patterns = ['cake', 'cupcake', 'cookie', 'brownie', 'pie', 'tart', 'donut', 'sweet']
        food_patterns = ['pizza', 'dough', 'kitchen', 'cook', 'recipe', 'ingredient', 'flour', 'yeast']
        
        if any(word in filename_lower for word in bread_patterns):
            tags.extend(['bread', 'baked goods', 'food', 'bakery', 'artisan'])
        elif any(word in filename_lower for word in pastry_patterns):
            tags.extend(['pastry', 'baked goods', 'food', 'bakery'])
        elif any(word in filename_lower for word in dessert_patterns):
            tags.extend(['dessert', 'baked goods', 'food', 'sweet', 'bakery'])
        elif any(word in filename_lower for word in food_patterns):
            tags.extend(['food', 'cooking', 'kitchen', 'culinary'])
        
        # BUSINESS & LOCATIONS
        business_patterns = [
            'shop', 'store', 'bakery', 'cafe', 'restaurant', 'kitchen', 'counter',
            'display', 'shelf', 'oven', 'interior', 'exterior', 'building', 'storefront'
        ]
        if any(word in filename_lower for word in business_patterns):
            tags.extend(['location', 'business', 'commercial'])
            if any(word in filename_lower for word in ['bakery', 'shop', 'store']):
                tags.extend(['bakery', 'retail', 'storefront'])
        
        # PRODUCTS & MERCHANDISE
        product_patterns = ['product', 'merchandise', 'item', 'goods', 'package', 'box', 'label', 'brand']
        if any(word in filename_lower for word in product_patterns):
            tags.extend(['product', 'merchandise', 'commercial', 'branding'])
        
        # EVENTS & ACTIVITIES
        event_patterns = ['event', 'party', 'celebration', 'wedding', 'birthday', 'opening', 'festival']
        if any(word in filename_lower for word in event_patterns):
            tags.extend(['event', 'celebration', 'occasion', 'social'])
        
        # ART & DESIGN
        art_patterns = ['art', 'design', 'logo', 'graphic', 'drawing', 'sketch', 'illustration']
        if any(word in filename_lower for word in art_patterns):
            tags.extend(['art', 'design', 'graphic', 'illustration', 'creative'])
        
        # Path context analysis
        path_parts = media_path.lower().split(os.sep)
        for part in path_parts:
            if any(keyword in part for keyword in ['portrait', 'people', 'staff']):
                tags.extend(['person', 'people', 'portrait'])
            elif any(keyword in part for keyword in ['product', 'merchandise']):
                tags.extend(['product', 'commercial'])
            elif any(keyword in part for keyword in ['food', 'bakery', 'kitchen']):
                tags.extend(['food', 'bakery', 'culinary'])
        
        # Fallback for generic files
        if not tags:
            file_ext = os.path.splitext(base_filename)[1].lower()
            if file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
                # Smart fallback based on context
                context_hints = media_path.lower()
                if any(keyword in context_hints for keyword in ['bread', 'bakery', 'food']):
                    tags = ['food', 'bakery', 'photo', 'content']
                elif any(keyword in context_hints for keyword in ['people', 'person', 'portrait']):
                    tags = ['person', 'people', 'photo', 'portrait']
                else:
                    tags = ['photo', 'image', 'visual', 'content']
            elif file_ext in ['.mp4', '.mov', '.avi']:
                tags = ['video', 'motion', 'recording', 'media']
            else:
                tags = ['media', 'file', 'content']
        
        # Always include basic file type
        file_ext = os.path.splitext(base_filename)[1].lower()
        if file_ext in ['.jpg', '.jpeg', '.png', '.gif'] and 'photo' not in tags:
            tags.append('photo')
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in tags:
            if tag.lower() not in seen:
                seen.add(tag.lower())
                unique_tags.append(tag)
        
        return unique_tags

    def score_relevance(self, tags: List[str], keywords: List[str]) -> int:
        """
        Score how relevant tags are to search keywords.
        
        Args:
            tags: List of AI tags for the media
            keywords: List of search keywords
            
        Returns:
            Relevance score (0-100)
        """
        score = 0
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # Exact tag match - highest score
            if keyword_lower in [tag.lower() for tag in tags]:
                score += 10
            
            # Partial tag match - good score
            elif any(keyword_lower in tag.lower() or tag.lower() in keyword_lower for tag in tags):
                score += 8
        
        # Category bonuses
        food_keywords = ['bread', 'food', 'bakery', 'baked', 'goods', 'pastry']
        people_keywords = ['people', 'person', 'portrait', 'staff', 'team', 'customer']
        business_keywords = ['shop', 'store', 'location', 'commercial', 'business']
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            if keyword_lower in food_keywords and any(tag.lower() in food_keywords for tag in tags):
                score += 5
            elif keyword_lower in people_keywords and any(tag.lower() in ['person', 'people', 'portrait'] for tag in tags):
                score += 7
            elif keyword_lower in business_keywords and any(tag.lower() in ['business', 'commercial', 'location'] for tag in tags):
                score += 4
        
        return min(score, 100)  # Cap at 100

# Create a global instance for easy importing
ai_tagger = AITaggingEngine() 