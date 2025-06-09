from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime

from crow_eye_api import models, schemas
from crow_eye_api.api.api_v1.dependencies import get_current_active_user, get_db

router = APIRouter()

# Mock templates data for demo purposes
MOCK_TEMPLATES = [
    {
        "id": "template_1",
        "name": "Motivational Monday",
        "description": "Weekly motivation template for Monday posts",
        "category": "motivation",
        "platforms": ["instagram", "facebook", "twitter"],
        "template": {
            "caption_template": "Monday Motivation: {quote} 💪\n\n{personal_message}\n\n#MondayMotivation #Inspiration #Goals",
            "hashtag_template": "#MondayMotivation #Inspiration #Goals #Success #Mindset",
            "formatting": {
                "vertical_optimization": True,
                "caption_overlay": True,
                "overlay_position": "bottom",
                "overlay_font_size": "large"
            }
        },
        "variables": [
            {
                "name": "quote",
                "type": "text",
                "required": True,
                "options": None
            },
            {
                "name": "personal_message",
                "type": "text",
                "required": False,
                "options": None
            }
        ],
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "user_id": "user_1"
    }
]

@router.post("/", response_model=schemas.Template)
async def create_template(
    template: schemas.TemplateCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new post template."""
    template_id = str(uuid.uuid4())
    mock_template = {
        "id": template_id,
        "user_id": str(current_user.id),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        **template.dict()
    }
    return schemas.Template(**mock_template)

@router.get("/", response_model=List[schemas.Template])
async def get_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all templates for the current user."""
    templates = MOCK_TEMPLATES.copy()
    
    if category:
        templates = [t for t in templates if t["category"] == category]
    
    if platform:
        templates = [t for t in templates if platform in t["platforms"]]
    
    return [schemas.Template(**template) for template in templates]

@router.post("/{template_id}/apply", response_model=schemas.TemplateApplyResponse)
async def apply_template(
    template_id: str,
    apply_request: schemas.TemplateApplyRequest,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Apply a template with variable substitution."""
    template = None
    for t in MOCK_TEMPLATES:
        if t["id"] == template_id:
            template = t
            break
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    caption_template = template["template"]["caption_template"]
    hashtag_template = template["template"].get("hashtag_template", "")
    
    for var_name, var_value in apply_request.variables.items():
        placeholder = "{" + var_name + "}"
        caption_template = caption_template.replace(placeholder, str(var_value))
        if hashtag_template:
            hashtag_template = hashtag_template.replace(placeholder, str(var_value))
    
    return schemas.TemplateApplyResponse(
        caption=caption_template,
        hashtags=hashtag_template if hashtag_template else None,
        formatted_content={
            "formatting": template["template"].get("formatting", {}),
            "media_id": apply_request.media_id,
            "platforms": template["platforms"]
        }
    ) 