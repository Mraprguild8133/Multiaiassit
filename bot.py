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
