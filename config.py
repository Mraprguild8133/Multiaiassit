import os
from dotenv import load_dotenv

class Config:
    def __init__(self):
        # Load environment variables from .env file if it exists
        load_dotenv()
        
        # Telegram Bot Token
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.telegram_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
        
        # AI Service API Keys
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self.deepai_api_key = os.getenv("DEEPAI_API_KEY")
        
        # Validate at least one AI service is configured
        if not any([self.gemini_api_key, self.deepseek_api_key, self.deepai_api_key]):
            raise ValueError("At least one AI service API key must be configured")
        
        # Bot Configuration
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT", "30"))
        self.max_message_length = int(os.getenv("MAX_MESSAGE_LENGTH", "4000"))
        
        # Logging level
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
    
    def validate_config(self):
        """Validate configuration and log warnings for missing services"""
        import logging
        logger = logging.getLogger(__name__)
        
        services_status = []
        
        if self.gemini_api_key:
            services_status.append("✅ Gemini AI - Configured")
        else:
            services_status.append("❌ Gemini AI - API key missing")
            logger.warning("Gemini API key not configured")
        
        if self.deepseek_api_key:
            services_status.append("✅ Deepseek - Configured")
        else:
            services_status.append("❌ Deepseek - API key missing")
            logger.warning("Deepseek API key not configured")
        
        if self.deepai_api_key:
            services_status.append("✅ DeepAI - Configured")
        else:
            services_status.append("❌ DeepAI - API key missing")
            logger.warning("DeepAI API key not configured")
        
        logger.info("AI Services Configuration:")
        for status in services_status:
            logger.info(f"  {status}")
        
        return services_status
