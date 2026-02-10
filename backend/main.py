from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import logging
import os


from .config import settings
from .database import engine, Base, get_db
from .chat_routes import router as chat_router
from .admin_routes import router as admin_router
from .migrations import sync_schema

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# Custom Swagger UI CSS matching frontend theme
CUSTOM_SWAGGER_CSS = """
/* Custom Theme - Matching Chatbot Frontend */
.swagger-ui .topbar { 
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 12px 0;
}
.swagger-ui .topbar .download-url-wrapper .select-label span { color: #fff; }
.swagger-ui .topbar .download-url-wrapper .download-url-input { border-color: rgba(255,255,255,0.3); }
.swagger-ui .info .title { 
    color: #667eea;
    font-weight: 700;
}
.swagger-ui .info .description {
    color: #555;
}
.swagger-ui .opblock.opblock-post { 
    border-color: #667eea; 
    background: rgba(102, 126, 234, 0.05);
}
.swagger-ui .opblock.opblock-post .opblock-summary-method { 
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.swagger-ui .opblock.opblock-get { 
    border-color: #49cc90; 
    background: rgba(73, 204, 144, 0.05);
}
.swagger-ui .opblock.opblock-get .opblock-summary-method { 
    background: linear-gradient(135deg, #3dbb86 0%, #49cc90 100%);
}
.swagger-ui .opblock.opblock-put { 
    border-color: #fca130; 
    background: rgba(252, 161, 48, 0.05);
}
.swagger-ui .opblock.opblock-delete { 
    border-color: #f93e3e; 
    background: rgba(249, 62, 62, 0.05);
}
.swagger-ui .btn.execute { 
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-color: #667eea;
}
.swagger-ui .btn.execute:hover {
    background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
}
.swagger-ui .btn.authorize { 
    color: #667eea; 
    border-color: #667eea; 
}
.swagger-ui .btn.authorize:hover {
    background: rgba(102, 126, 234, 0.1);
}
.swagger-ui .btn.authorize svg { fill: #667eea; }
.swagger-ui .response-col_status { color: #667eea; }
.swagger-ui section.models { border-color: #667eea; }
.swagger-ui section.models h4 { color: #667eea; }
.swagger-ui .model-box { background: rgba(102, 126, 234, 0.03); }
.swagger-ui .opblock-tag { 
    border-bottom: 1px solid rgba(102, 126, 234, 0.2);
}
.swagger-ui .opblock-tag:hover { background: rgba(102, 126, 234, 0.05); }
.swagger-ui .opblock .opblock-summary-path { color: #333; }
.swagger-ui .opblock .opblock-summary-description { color: #666; }
.swagger-ui a.nostyle { color: #667eea; }
.swagger-ui .model-title { color: #667eea; }
body {
    background: #fafafa;
}
.swagger-ui .scheme-container {
    background: #fff;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
/* Custom scrollbar */
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: #f1f1f1; }
::-webkit-scrollbar-thumb { 
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover { background: #764ba2; }
"""

# Initialize FastAPI app (disable default docs to use custom)
app = FastAPI(
    title="PE/VC Chatbot API",
    description="Private LLM-powered chatbot for investor portal",
    version="1.0.0",
    docs_url=None,  # Disable default docs
    redoc_url=None,  # Disable redoc
    openapi_url="/openapi.json"
)

# Custom Swagger UI endpoint with styling
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return HTMLResponse(
        content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>PE/VC Chatbot API - Documentation</title>
            <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
            <link rel="icon" type="image/png" href="https://fastapi.tiangolo.com/img/favicon.png">
            <style>{CUSTOM_SWAGGER_CSS}</style>
        </head>
        <body>
            <div id="swagger-ui"></div>
            <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
            <script>
                SwaggerUIBundle({{
                    url: '/openapi.json',
                    dom_id: '#swagger-ui',
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIBundle.SwaggerUIStandalonePreset
                    ],
                    layout: "BaseLayout",
                    deepLinking: true,
                    showExtensions: true,
                    showCommonExtensions: true
                }});
            </script>
        </body>
        </html>
        """,
        media_type="text/html"
    )

# Build CORS origins list
cors_origins = [
    "http://localhost:3000",          # React dev server
    "http://localhost:8001",          # FastAPI itself
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8001",
    "https://chat-bot-phi-seven.vercel.app",  # Deployed Vercel frontend
]
# Add deployed frontend URL if set
if settings.FRONTEND_URL and settings.FRONTEND_URL not in cors_origins:
    cors_origins.append(settings.FRONTEND_URL)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router)
app.include_router(admin_router)

# Admin Portal
@app.get("/admin-portal", response_class=HTMLResponse)
async def admin_portal():
    """Serve the admin portal UI"""
    admin_path = os.path.join(os.path.dirname(__file__), "static", "admin.html")
    return FileResponse(admin_path, media_type="text/html")

# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "PE/VC Chatbot API",
        "version": "1.0.0",
        "docs": "/docs",
        "admin": "/admin",
        "health": "/health"
    }

# Health check endpoint
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint
    Verifies API and database are running
    """
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        
        return {
            "status": "ok",
            "service": "chatbot-api",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "database": "disconnected"
        }, 500

# Startup event
import asyncio

async def initialize_database():
    """Background task to initialize database without blocking startup"""
    try:
        logger.info("Background: Initializing database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Background: Database tables creation completed")

        logger.info("Background: Synchronizing database schema...")
        sync_schema(engine, Base)
        logger.info("✓ Background: Schema synchronization completed successfully")
    except Exception as e:
        logger.error(f"✗ Background: Database initialization failed: {e}")

@app.on_event("startup")
async def startup_event():
    logger.info("Chatbot API starting up...")
    
    # Fire and forget database initialization so we bind to port immediately
    asyncio.create_task(initialize_database())
    
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Database: {settings.DATABASE_URL.split('@') if '@' in settings.DATABASE_URL else 'unknown'}")
    logger.info(f"LLM Provider: Groq API")
    logger.info(f"LLM Model: {settings.GROQ_MODEL}")
    logger.info(f"Frontend URL: {settings.FRONTEND_URL}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Chatbot API shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.DEBUG
    )
