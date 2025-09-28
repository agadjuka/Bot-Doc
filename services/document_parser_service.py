"""
Document Parser Service for extracting company information using Gemini AI
"""
import json
import asyncio
import os
from typing import Dict, Any, Optional
import google.generativeai as genai
from google.oauth2 import service_account

from config.prompts import PromptManager

# ВРЕМЕННЫЙ ДЕБАГ - можно удалить после отладки
try:
    from debug_gemini_logger import log_gemini_request, log_gemini_response
    DEBUG_GEMINI = True
except ImportError:
    DEBUG_GEMINI = False
    def log_gemini_request(*args, **kwargs): return ""
    def log_gemini_response(*args, **kwargs): return ""


class DocumentParserService:
    """Service for parsing company information from text using Gemini AI"""
    
    def __init__(self, gemini_api_key: str = None):
        """
        Initialize the Document Parser Service using Google Cloud authentication
        
        Args:
            gemini_api_key: Deprecated parameter, now uses Google Cloud authentication
        """
        self.prompt_manager = PromptManager()
        
        # Get credentials file path
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not credentials_path:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS is required")
        
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"Credentials file not found: {credentials_path}")
        
        # Load service account credentials
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/generative-language']
        )
        
        # Configure Gemini with service account credentials
        genai.configure(credentials=credentials)
        self.model = genai.GenerativeModel("gemini-2.5-flash")
        
        # Define the required fields for extraction
        self.required_fields = [
            "COMPANY_FULL_NAME",
            "COMPANY_SHORT_NAME", 
            "INN",
            "KPP",
            "OGRN",
            "LEGAL_ADDRESS",
            "DIRECTOR_FULL_NAME",
            "DIRECTOR_POSITION"
        ]
    
    async def parse_company_info(self, text: str) -> Dict[str, Any]:
        """
        Parse company information from text using Gemini AI
        
        Args:
            text: Raw text containing company information
            
        Returns:
            Dictionary with extracted company information
        """
        try:
            # Create the prompt for Gemini using PromptManager
            fields_list = ", ".join(self.required_fields)
            prompt = self.prompt_manager.get_company_info_extraction_prompt(fields_list, text)
            
            # ВРЕМЕННЫЙ ДЕБАГ - логируем запрос
            request_file = ""
            if DEBUG_GEMINI:
                request_file = log_gemini_request(
                    prompt=prompt,
                    service_name="DocumentParserService",
                    user_id=None,
                    additional_info={"text_length": len(text), "required_fields": self.required_fields}
                )
            
            # Generate response using Gemini
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.model.generate_content(prompt)
            )
            
            # Parse the JSON response
            response_text = response.text.strip()
            
            # ВРЕМЕННЫЙ ДЕБАГ - логируем ответ
            if DEBUG_GEMINI and request_file:
                log_gemini_response(
                    response=response_text,
                    request_filepath=request_file,
                    success=True
                )
            
            # Try to extract JSON from the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                data = json.loads(json_text)
            else:
                # If no JSON found, try to parse the whole response
                data = json.loads(response_text)
            
            # Validate that we have the required fields
            result = {}
            for field in self.required_fields:
                result[field] = data.get(field, None)
            
            print(f"✅ Данные успешно извлечены: {len([v for v in result.values() if v is not None])} из {len(self.required_fields)} полей")
            return result
            
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка парсинга JSON от Gemini: {e}")
            print(f"Ответ Gemini: {response_text}")
            
            # ВРЕМЕННЫЙ ДЕБАГ - логируем ошибку парсинга
            if DEBUG_GEMINI and request_file:
                log_gemini_response(
                    response=response_text,
                    request_filepath=request_file,
                    success=False,
                    error_message=f"JSON Decode Error: {e}"
                )
            
            # Return empty data with null values
            return {field: None for field in self.required_fields}
            
        except Exception as e:
            print(f"❌ Ошибка при анализе реквизитов: {e}")
            
            # ВРЕМЕННЫЙ ДЕБАГ - логируем ошибку
            if DEBUG_GEMINI and request_file:
                log_gemini_response(
                    response="",
                    request_filepath=request_file,
                    success=False,
                    error_message=str(e)
                )
            
            # Return empty data with null values
            return {field: None for field in self.required_fields}
    
