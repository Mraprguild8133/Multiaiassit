import asyncio
import aiohttp
import logging
import json
import os
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

class AIServiceManager:
    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.together_api_key = os.getenv("TOGETHER_API_KEY")
        
        # Initialize Gemini client
        if self.gemini_api_key:
            self.gemini_client = genai.Client(api_key=self.gemini_api_key)
        else:
            self.gemini_client = None
            logger.warning("Gemini API key not found")
    
    async def query_all_services(self, message: str, timeout: int = 20):
        """Query all AI services simultaneously"""
        tasks = [
            self.query_gemini(message, timeout),
            self.query_together(message, timeout)
        ]
        
        # Run all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            'gemini': results[0] if not isinstance(results[0], Exception) else {'success': False, 'error': str(results[0])},
            'together': results[1] if not isinstance(results[1], Exception) else {'success': False, 'error': str(results[1])}
        }
    
    async def query_gemini(self, message: str, timeout: int = 30):
        """Query Gemini AI service"""
        try:
            if not self.gemini_client:
                return {'success': False, 'error': 'Gemini API key not configured'}
            
            # Run Gemini query in executor to avoid blocking
            loop = asyncio.get_event_loop()
            
            def _sync_gemini_query():
                response = self.gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=message
                )
                return response.text or "No response received"
            
            response_text = await asyncio.wait_for(
                loop.run_in_executor(None, _sync_gemini_query),
                timeout=timeout
            )
            
            return {'success': True, 'response': response_text}
            
        except asyncio.TimeoutError:
            logger.error("Gemini API timeout")
            return {'success': False, 'error': 'Request timeout'}
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return {'success': False, 'error': f'API error: {str(e)}'}
    
    async def query_together(self, message: str, timeout: int = 30):
        """Query Together.ai service"""
        try:
            if not self.together_api_key:
                return {'success': False, 'error': 'Together API key not configured'}
            
            url = "https://api.together.xyz/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.together_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo",
                "messages": [
                    {"role": "user", "content": message}
                ],
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        response_text = data['choices'][0]['message']['content']
                        return {'success': True, 'response': response_text}
                    else:
                        error_text = await response.text()
                        logger.error(f"Together API error {response.status}: {error_text}")
                        return {'success': False, 'error': f'API error {response.status}'}
                        
        except asyncio.TimeoutError:
            logger.error("Together API timeout")
            return {'success': False, 'error': 'Request timeout'}
        except Exception as e:
            logger.error(f"Together API error: {e}")
            return {'success': False, 'error': f'API error: {str(e)}'}
    

