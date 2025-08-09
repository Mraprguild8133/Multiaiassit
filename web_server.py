"""
Web server for bot status, webhook, and dashboard
"""
import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from ai_services import AIServiceManager
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Multi-AI Telegram Bot API", version="1.0.0")

# Global variables to track bot status
bot_status = {
    "running": False,
    "start_time": None,
    "last_update": None,
    "services": {
        "gemini": False,
        "together": False
    }
}

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the main dashboard"""
    html_file = Path("index.html")
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text(), status_code=200)
    else:
        return HTMLResponse(content="<h1>Multi-AI Telegram Bot</h1><p>Dashboard not found</p>", status_code=200)

@app.get("/status")
async def get_bot_status():
    """Get current bot and services status"""
    # Test AI services
    ai_manager = AIServiceManager()
    
    # Quick test for Gemini
    gemini_working = False
    if ai_manager.gemini_client:
        try:
            # Simple test - just check if client is initialized
            gemini_working = True
        except:
            gemini_working = False
    
    # Quick test for Together.ai
    together_working = bool(ai_manager.together_api_key)
    
    bot_status["services"]["gemini"] = gemini_working
    bot_status["services"]["together"] = together_working
    bot_status["last_update"] = datetime.now().isoformat()
    
    return JSONResponse({
        "bot_running": True,  # If this endpoint responds, server is running
        "services": bot_status["services"],
        "uptime": bot_status.get("start_time"),
        "last_check": bot_status["last_update"],
        "timestamp": datetime.now().isoformat()
    })

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Handle Telegram webhook updates"""
    try:
        # Get the JSON data from the request
        update_data = await request.json()
        logger.info(f"Received webhook update: {json.dumps(update_data, indent=2)}")
        
        # Here you would process the update with your bot
        # For now, we'll just log it and return success
        
        return JSONResponse({"status": "ok"})
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/services/test")
async def test_services():
    """Test all AI services with a simple query"""
    ai_manager = AIServiceManager()
    
    try:
        # Test with a simple message
        test_message = "Hello, this is a test."
        responses = await ai_manager.query_all_services(test_message, timeout=10)
        
        return JSONResponse({
            "test_message": test_message,
            "responses": responses,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Service test error: {e}")
        return JSONResponse({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, status_code=500)

@app.get("/config")
async def get_config():
    """Get current configuration (without sensitive data)"""
    config = Config()
    
    return JSONResponse({
        "bot_configured": bool(config.telegram_bot_token),
        "services_configured": {
            "gemini": bool(config.gemini_api_key),
            "together": bool(config.together_api_key)
        },
        "environment": os.getenv("NODE_ENV", "development"),
        "timestamp": datetime.now().isoformat()
    })

@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    logger.info("Starting Multi-AI Telegram Bot Web Server...")
    bot_status["running"] = True
    bot_status["start_time"] = datetime.now().isoformat()
    logger.info("Web server started successfully!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Multi-AI Telegram Bot Web Server...")
    bot_status["running"] = False

if __name__ == "__main__":
    # Run the web server
    port = int(os.getenv("PORT", 5000))
    logger.info(f"Starting web server on port {port}")
    
    uvicorn.run(
        "web_server:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )
    # Start the bot
        logger.info("Bot is running. Press Ctrl+C to stop.")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    bot = TelegramBot()
    bot.run()
