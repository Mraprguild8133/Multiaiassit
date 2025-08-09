import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from ai_services import AIServiceManager
from config import Config

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

class MultiAIBot:
    def __init__(self):
        self.config = Config()
        self.ai_manager = AIServiceManager()
        self.telegram_app = None
        self.web_app = None
        self.bot_status = {
            "running": False,
            "start_time": None,
            "last_update": None,
            "services": {
                "gemini": False,
                "together": False,
            },
        }

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
            "/help - Show help information\n"
            "/status - Check bot status"
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
            "Commands:\n"
            "/start - Welcome message\n"
            "/help - This message\n"
            "/status - Check bot and services status\n\n"
            "Just start chatting - I'm here to help!"
        )
        await update.message.reply_text(help_message)

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        await self.check_services_status()
        status_message = (
            "🤖 <b>Bot Status</b>\n\n"
            f"• <b>Uptime:</b> {self.format_uptime()}\n"
            f"• <b>Last update:</b> {self.bot_status['last_update'] or 'N/A'}\n\n"
            "<b>Services Status</b>\n"
            f"• 🔷 Gemini AI: {'✅ Working' if self.bot_status['services']['gemini'] else '❌ Not working'}\n"
            f"• 🟠 Together.ai: {'✅ Working' if self.bot_status['services']['together'] else '❌ Not working'}\n\n"
            "✨ <i>Send any message to test the services</i>"
        )
        await update.message.reply_text(status_message, parse_mode="HTML")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user messages and query all AI services"""
        if not update.message or not update.message.text:
            return

        user_message = update.message.text
        user_name = update.effective_user.first_name if update.effective_user else "User"

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

            # Update service status based on responses
            self.bot_status["services"]["gemini"] = responses["gemini"]["success"]
            self.bot_status["services"]["together"] = responses["together"]["success"]
            self.bot_status["last_update"] = datetime.now().isoformat()

            # Format and send the combined response
            formatted_response = self.format_responses(responses)
            logger.info(f"Formatted response length: {len(formatted_response)}")

            # Delete processing message and send results
            try:
                await processing_msg.delete()
                await update.message.reply_text(formatted_response, parse_mode="HTML")
            except Exception as e:
                logger.error(f"Error sending formatted response: {e}")
                await update.message.reply_text(formatted_response)

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
        if responses["gemini"]["success"]:
            response_text = responses["gemini"]["response"]
            if len(response_text) > 800:
                response_text = response_text[:800] + "... (truncated)"
            formatted += "🔷 <b>Gemini AI:</b>\n"
            formatted += f"{response_text}\n\n"
        else:
            formatted += "🔷 <b>Gemini AI:</b> ❌ Error - "
            formatted += f"{responses['gemini']['error']}\n\n"

        # Together.ai response
        if responses["together"]["success"]:
            response_text = responses["together"]["response"]
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

    async def check_services_status(self):
        """Check the status of all AI services"""
        # Test Gemini
        gemini_working = False
        if self.ai_manager.gemini_client:
            try:
                # Simple test - just check if client is initialized
                gemini_working = True
            except:
                gemini_working = False

        # Test Together.ai
        together_working = bool(self.ai_manager.together_api_key)

        self.bot_status["services"]["gemini"] = gemini_working
        self.bot_status["services"]["together"] = together_working
        self.bot_status["last_update"] = datetime.now().isoformat()

    def format_uptime(self):
        """Format the uptime for display"""
        if not self.bot_status["start_time"]:
            return "Not available"
        
        start_time = datetime.fromisoformat(self.bot_status["start_time"])
        uptime = datetime.now() - start_time
        
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return f"{days}d {hours}h {minutes}m {seconds}s"

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Log errors caused by updates"""
        logger.error(f"Exception while handling an update: {context.error}")

    async def setup_telegram(self):
        """Set up the Telegram bot"""
        self.telegram_app = (
            Application.builder().token(self.config.telegram_token).build()
        )

        # Add handlers
        self.telegram_app.add_handler(CommandHandler("start", self.start_command))
        self.telegram_app.add_handler(CommandHandler("help", self.help_command))
        self.telegram_app.add_handler(CommandHandler("status", self.status_command))
        self.telegram_app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )

        # Add error handler
        self.telegram_app.add_error_handler(self.error_handler)

    async def setup_web(self):
        """Set up the web server"""
        self.web_app = FastAPI(title="Multi-AI Telegram Bot API", version="1.0.0")

        # Add routes
        self.web_app.get("/", response_class=HTMLResponse)(self.dashboard)
        self.web_app.get("/status")(self.web_status)
        self.web_app.get("/health")(self.health_check)
        self.web_app.post("/webhook")(self.telegram_webhook)
        self.web_app.get("/services/test")(self.test_services)
        self.web_app.get("/config")(self.get_config)

    async def dashboard(self):
        """Serve the main dashboard"""
        html_file = Path("index.html")
        if html_file.exists():
            return HTMLResponse(content=html_file.read_text(), status_code=200)
        return HTMLResponse(
            content="<h1>Multi-AI Telegram Bot</h1><p>Dashboard not found</p>",
            status_code=200,
        )

    async def web_status(self):
        """Get current bot and services status"""
        await self.check_services_status()
        return JSONResponse(
            {
                "bot_running": True,
                "services": self.bot_status["services"],
                "uptime": self.format_uptime(),
                "last_check": self.bot_status["last_update"],
                "timestamp": datetime.now().isoformat(),
            }
        )

    async def health_check(self):
        """Health check endpoint for monitoring"""
        return JSONResponse(
            {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
            }
        )

    async def telegram_webhook(self, request: Request):
        """Handle Telegram webhook updates"""
        try:
            update_data = await request.json()
            logger.info(f"Received webhook update: {json.dumps(update_data, indent=2)}")
            
            if self.telegram_app:
                update = Update.de_json(update_data, self.telegram_app.bot)
                await self.telegram_app.process_update(update)
            
            return JSONResponse({"status": "ok"})
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def test_services(self):
        """Test all AI services with a simple query"""
        try:
            test_message = "Hello, this is a test."
            responses = await self.ai_manager.query_all_services(test_message, timeout=10)
            
            return JSONResponse(
                {
                    "test_message": test_message,
                    "responses": responses,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"Service test error: {e}")
            return JSONResponse(
                {"error": str(e), "timestamp": datetime.now().isoformat()},
                status_code=500,
            )

    async def get_config(self):
        """Get current configuration (without sensitive data)"""
        return JSONResponse(
            {
                "bot_configured": bool(self.config.telegram_token),
                "services_configured": {
                    "gemini": bool(self.config.gemini_api_key),
                    "together": bool(self.config.together_api_key),
                },
                "environment": os.getenv("NODE_ENV", "development"),
                "timestamp": datetime.now().isoformat(),
            }
        )

    async def start(self):
        """Start both the Telegram bot and web server"""
        self.bot_status["running"] = True
        self.bot_status["start_time"] = datetime.now().isoformat()

        await self.setup_telegram()
        await self.setup_web()

        # Start Telegram bot in background
        telegram_task = asyncio.create_task(
            self.telegram_app.run_polling(allowed_updates=Update.ALL_TYPES)
        )

        # Start web server
        port = int(os.getenv("PORT", 5000))
        config = uvicorn.Config(
            app=self.web_app,
            host="0.0.0.0",
            port=port,
            log_level="info",
        )
        server = uvicorn.Server(config)
        
        await server.serve()

        # Cleanup if needed
        telegram_task.cancel()
        try:
            await telegram_task
        except asyncio.CancelledError:
            pass

    async def stop(self):
        """Stop the application"""
        self.bot_status["running"] = False
        if self.telegram_app:
            await self.telegram_app.stop()
            await self.telegram_app.shutdown()


async def main():
    bot = MultiAIBot()
    try:
        await bot.start()
    except KeyboardInterrupt:
        await bot.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())