# Multi-AI Telegram Bot

## Overview

This is a Telegram bot that integrates with multiple AI services (Gemini AI and Together.ai) to provide simultaneous responses from both platforms. The bot accepts user messages and queries all configured AI services concurrently, returning responses from each service in a structured format. The system is designed for high availability with graceful error handling when individual AI services are unavailable.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Bot Framework
- **Telegram Bot Architecture**: Built using `python-telegram-bot` library with async/await patterns for non-blocking operations
- **Command Handling**: Implements command handlers for `/start` and `/help` commands, plus message handlers for general text processing
- **Concurrent Processing**: Uses `asyncio.gather()` to query multiple AI services simultaneously, reducing overall response time

### AI Service Integration
- **Multi-Service Manager**: Centralized `AIServiceManager` class handles integration with two AI platforms:
  - Google Gemini AI (using official `google.genai` SDK)
  - Together.ai (via HTTP API with Llama 3.2 model)
- **Async HTTP Client**: Uses `aiohttp` for non-blocking HTTP requests to external AI APIs
- **Error Isolation**: Individual service failures don't affect other services - each runs independently with timeout protection

### Configuration Management
- **Environment-Based Config**: Uses environment variables for all sensitive data (API keys, tokens)
- **Validation Layer**: Validates configuration at startup, ensuring at least one AI service is properly configured
- **Flexible Service Setup**: Allows partial configuration - bot operates with any subset of the two AI services
- **Dotenv Support**: Loads configuration from `.env` files for development environments

### Error Handling and Resilience
- **Timeout Protection**: 30-second timeout per AI service to prevent hanging requests
- **Exception Isolation**: Service-specific exceptions are caught and reported without crashing the entire bot
- **Graceful Degradation**: Bot continues operating even if some AI services are unavailable
- **Comprehensive Logging**: Structured logging for monitoring and debugging service health

### Message Processing Flow
1. User sends message to Telegram bot
2. Bot validates and processes the message
3. Both AI services (Gemini and Together.ai) are queried concurrently
4. Results are collected and formatted with clear service attribution
5. Combined response is sent back to user showing responses from both services

## External Dependencies

### AI Services
- **Google Gemini AI**: Requires `GEMINI_API_KEY` environment variable
- **Together.ai API**: Requires `TOGETHER_API_KEY` environment variable

### Telegram Platform
- **Telegram Bot API**: Requires `TELEGRAM_BOT_TOKEN` for bot authentication and message handling

### Python Libraries
- **python-telegram-bot**: Official Telegram bot framework for Python
- **google-genai**: Official Google SDK for Gemini AI integration
- **aiohttp**: Async HTTP client for external API calls
- **python-dotenv**: Environment variable management for configuration
- **asyncio**: Built-in Python library for concurrent programming

### Configuration Requirements
- At least one AI service API key must be configured for the bot to function
- Telegram bot token is mandatory for basic operation
- Optional environment variables for timeout and message length limits