from typing import Dict, Any
from pydantic import BaseModel

class PlatformRequirementsResponse(BaseModel):
    platforms: Dict[str, Any]
    last_updated: str 