FROM python:3.11-slim

WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN pip install python-telegram-bot==20.7 google-genai==0.6.0 aiohttp==3.9.1 python-dotenv==1.0.0 fastapi==0.104.1 uvicorn==0.24.0

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=5000

# Expose port
EXPOSE 5000

# Command to run the application
CMD ["python", "web_server.py"]