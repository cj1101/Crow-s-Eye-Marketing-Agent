import os 
import uvicorn 
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from .routers import highlights

app = FastAPI(
    title="Crow's Eye Marketing Platform API",
    description="AI-powered social media content creation and automation platform",
    version="5.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(highlights.router, prefix="/api/highlights", tags=["highlights"])

@app.get("/") 
def read_root(): 
    return {
        "message": "Crow's Eye Marketing Platform API", 
        "version": "5.0.0",
        "features": [
            "Long-form highlight generation",
            "AI-powered video analysis",
            "Cost-optimized processing"
        ]
    } 
 
@app.get("/health") 
def health(): 
    return {"status": "healthy"} 
 
if __name__ == "__main__": 
    port = int(os.environ.get("PORT", 8000)) 
    uvicorn.run(app, host="0.0.0.0", port=port) 
