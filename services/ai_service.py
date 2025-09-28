"""
AI service for basic AI operations using Google Gemini
Template version - simplified for basic bot functionality
"""
import json
import asyncio
import os
from typing import Dict, Any, Optional
import google.generativeai as genai
from google.oauth2 import service_account

from config.settings import BotConfig
from config.prompts import PromptManager

# ВРЕМЕННЫЙ ДЕБАГ - можно удалить после отладки
try:
    from debug_gemini_logger import log_gemini_request, log_gemini_response
    DEBUG_GEMINI = True
except ImportError:
    DEBUG_GEMINI = False
    def log_gemini_request(*args, **kwargs): return ""
    def log_gemini_response(*args, **kwargs): return ""


class AIService:
    """Service for basic AI operations using Google Gemini - Template version"""
    
    def __init__(self, config: BotConfig, prompt_manager: PromptManager, model_type: str = None):
        self.config = config
        self.prompt_manager = prompt_manager
        self.model_type = model_type or config.DEFAULT_MODEL
        self._model = None
        self._initialize_gemini()
    
    def _initialize_gemini(self):
        """Initialize Google Gemini AI service using Google Cloud authentication"""
        try:
            # Get credentials file path
            credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if not credentials_path:
                print("❌ GOOGLE_APPLICATION_CREDENTIALS не установлена")
                raise ValueError("GOOGLE_APPLICATION_CREDENTIALS is required")
            
            if not os.path.exists(credentials_path):
                print(f"❌ Файл учетных данных не найден: {credentials_path}")
                raise FileNotFoundError(f"Credentials file not found: {credentials_path}")
            
            # Load service account credentials
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=['https://www.googleapis.com/auth/generative-language']
            )
            
            # Configure Gemini API with service account credentials
            genai.configure(credentials=credentials)
            
            # Get model name
            model_name = self.config.get_model_name(self.model_type)
            self._model = genai.GenerativeModel(model_name)
            
            print(f"✅ Gemini AI инициализирован: {model_name}")
            
        except Exception as e:
            print(f"❌ Ошибка инициализации Gemini AI: {e}")
            raise
    
    def get_current_model_info(self) -> dict:
        """Get information about current model"""
        return {
            "type": self.model_type,
            "name": self.config.get_model_name(self.model_type),
            "available_models": self.config.get_available_models()
        }
    
    async def get_ai_response(self, user_text: str, language: str = "en") -> str:
        """Get AI response for user text"""
        try:
            # Get prompt from PromptManager
            prompt = self.prompt_manager.get_ai_response_prompt(user_text, language)
            
            # ВРЕМЕННЫЙ ДЕБАГ - логируем запрос
            request_file = ""
            if DEBUG_GEMINI:
                request_file = log_gemini_request(
                    prompt=prompt,
                    service_name="AIService",
                    user_id=None,
                    additional_info={"user_text": user_text, "language": language}
                )
            
            # Generate response with timeout
            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda: self._model.generate_content(prompt)
                ),
                timeout=30.0  # 30 seconds timeout
            )
            
            response_text = response.text.strip()
            
            # ВРЕМЕННЫЙ ДЕБАГ - логируем ответ
            if DEBUG_GEMINI and request_file:
                log_gemini_response(
                    response=response_text,
                    request_filepath=request_file,
                    success=True
                )
            
            return response_text
            
        except Exception as e:
            print(f"❌ Ошибка получения AI ответа: {e}")
            
            # ВРЕМЕННЫЙ ДЕБАГ - логируем ошибку
            if DEBUG_GEMINI and request_file:
                log_gemini_response(
                    response="",
                    request_filepath=request_file,
                    success=False,
                    error_message=str(e)
                )
            
            return f"Извините, произошла ошибка при обработке вашего сообщения. Попробуйте позже."


class ReceiptAnalysisServiceCompat:
    """
    Compatibility wrapper for basic AI operations
    Template version - simplified for basic bot functionality
    """
    
    def __init__(self, ai_service: AIService, ai_factory=None):
        self.ai_service = ai_service
        self.ai_factory = ai_factory
    
    async def get_ai_response(self, user_text: str, language: str = "en") -> str:
        """Get AI response for user text"""
        return await self.ai_service.get_ai_response(user_text, language)


class AIServiceFactory:
    """Factory for creating AI services - Template version"""
    
    def __init__(self, config: BotConfig, prompt_manager: PromptManager):
        self.config = config
        self.prompt_manager = prompt_manager
        self._services = {}
    
    def get_service(self, model_type: str = None) -> AIService:
        """Get AI service for specified model type"""
        if model_type is None:
            model_type = self.config.DEFAULT_MODEL
        
        model_type = model_type.lower()
        
        # Check cache
        if model_type not in self._services:
            self._services[model_type] = AIService(
                self.config, 
                self.prompt_manager, 
                model_type
            )
            print(f"🏭 Создан AI сервис: {model_type.upper()}")
        
        return self._services[model_type]
    
    def get_default_service(self) -> AIService:
        """Get default AI service"""
        return self.get_service()
    
    def close_all_services(self):
        """Close all services"""
        self._services.clear()
        print("🔒 AI сервисы закрыты")