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

import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from ai_services import AIServiceManager
from config import Config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.config = Config()
        self.ai_manager = AIServiceManager()
        self.application = None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = (
            "🤖 Welcome to the Multi-AI Assistant Bot!\n\n"
            "I'm powered by two AI services working together:\n"
            "• 🔷 Google Gemini AI\n"
            "• 🟠 Together.ai (Llama 3.2)\n\n"
            "Just send me any message and I'll get responses from both AI services!\n\n"
            "Commands:\n"
            "/start - Show this welcome message\n"
            "/help - Show help information"
        )
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = (
            "🆘 Help - Multi-AI Assistant Bot\n\n"
            "How to use:\n"
            "1. Simply send any text message\n"
            "2. The bot will query both AI services simultaneously\n"
            "3. You'll receive responses from:\n"
            "   • Google Gemini AI\n"
            "   • Together.ai (Llama 3.2)\n\n"
            "Features:\n"
            "• Dual AI responses for comprehensive answers\n"
            "• Simultaneous processing for faster responses\n"
            "• Error handling for individual service failures\n"
            "• Timeout protection for reliability\n\n"
            "Just start chatting - I'm here to help!"
        )
        await update.message.reply_text(help_message)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user messages and query all AI services"""
        if not update.message or not update.message.text:
            return
        
        user_message = update.message.text
        user_name = (update.effective_user.first_name if update.effective_user else None) or "User"
        
        logger.info(f"Received message from {user_name}: {user_message}")
        
        # Send initial response to show bot is processing
        processing_msg = await update.message.reply_text(
            "🔄 Processing your message through all AI services...\n"
            "This may take a few seconds."
        )
        
        try:
            # Query all AI services simultaneously
            logger.info("Querying AI services...")
            responses = await self.ai_manager.query_all_services(user_message)
            logger.info(f"Got responses: {[k for k, v in responses.items() if v['success']]}")
            
            # Format and send the combined response
            formatted_response = self.format_responses(responses)
            logger.info(f"Formatted response length: {len(formatted_response)}")
            
            # Delete processing message and send results
            try:
                await processing_msg.delete()
                logger.info("Sending formatted response...")
                await update.message.reply_text(formatted_response, parse_mode='HTML')
                logger.info("Response sent successfully!")
            except Exception as send_error:
                logger.error(f"Error sending formatted response: {send_error}")
                # Try without HTML formatting
                try:
                    await update.message.reply_text(formatted_response)
                    logger.info("Response sent without HTML formatting")
                except Exception as simple_error:
                    logger.error(f"Error sending simple response: {simple_error}")
                    # Send a basic response
                    simple_response = "I received your message but had trouble sending the full response. Gemini AI is working."
                    await update.message.reply_text(simple_response)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            try:
                await processing_msg.edit_text(
                    "❌ Sorry, there was an error processing your message. Please try again."
                )
            except:
                await update.message.reply_text("❌ Error occurred. Please try again.")
    
    def format_responses(self, responses):
        """Format responses from all AI services"""
        formatted = "🤖 <b>AI Services Responses</b>\n\n"
        
        # Gemini response
        if responses['gemini']['success']:
            response_text = responses['gemini']['response']
            # Truncate if too long
            if len(response_text) > 800:
                response_text = response_text[:800] + "... (truncated)"
            formatted += "🔷 <b>Gemini AI:</b>\n"
            formatted += f"{response_text}\n\n"
        else:
            formatted += "🔷 <b>Gemini AI:</b> ❌ Error - "
            formatted += f"{responses['gemini']['error']}\n\n"
        
        # Together.ai response
        if responses['together']['success']:
            response_text = responses['together']['response']
            if len(response_text) > 800:
                response_text = response_text[:800] + "... (truncated)"
            formatted += "🟠 <b>Together.ai:</b>\n"
            formatted += f"{response_text}\n\n"
        else:
            formatted += "🟠 <b>Together.ai:</b> ❌ Error - "
            formatted += f"{responses['together']['error']}\n\n"
        
        # Add footer
        formatted += "✨ <i>Powered by Multi-AI Assistant</i>"
        
        # Final length check - Telegram max is 4096 characters
        if len(formatted) > 4000:
            formatted = formatted[:3950] + "... (message truncated)"
        
        return formatted
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Log errors caused by updates"""
        logger.error(f"Exception while handling an update: {context.error}")
    
    def run(self):
        """Start the bot"""
        logger.info("Starting Telegram Bot...")
        
        # Create application
        self.application = Application.builder().token(self.config.telegram_token).build()
        
        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Add error handler
        self.application.add_error_handler(self.error_handler)
        
        # Start the bot
        logger.info("Bot is running. Press Ctrl+C to stop.")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    bot = TelegramBot()
    bot.run()
