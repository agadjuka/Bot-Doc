"""
Document Parser Service for extracting company information using Gemini AI
"""
import json
import asyncio
import os
from typing import Dict, Any, Optional
import google.generativeai as genai
from google.oauth2 import service_account


class DocumentParserService:
    """Service for parsing company information from text using Gemini AI"""
    
    def __init__(self, gemini_api_key: str = None):
        """
        Initialize the Document Parser Service using Google Cloud authentication
        
        Args:
            gemini_api_key: Deprecated parameter, now uses Google Cloud authentication
        """
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
            # Create the prompt for Gemini
            fields_list = ", ".join(self.required_fields)
            prompt = f"""
Проанализируй текст с реквизитами компании. Извлеки следующие поля: {fields_list}.

Имена ключей в JSON должны быть ТОЧНО ТАКИМИ ЖЕ, как в списке выше. Если поле не найдено, используй null.

Текст для анализа:
{text}

Верни только валидный JSON без дополнительных комментариев или объяснений.
"""
            
            # Generate response using Gemini
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.model.generate_content(prompt)
            )
            
            # Parse the JSON response
            response_text = response.text.strip()
            
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
            # Return empty data with null values
            return {field: None for field in self.required_fields}
            
        except Exception as e:
            print(f"❌ Ошибка при анализе реквизитов: {e}")
            # Return empty data with null values
            return {field: None for field in self.required_fields}
    
    def get_required_fields(self) -> list:
        """Get list of required fields for extraction"""
        return self.required_fields.copy()
    
    def validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean extracted data
        
        Args:
            data: Extracted data dictionary
            
        Returns:
            Validated and cleaned data dictionary
        """
        validated_data = {}
        
        for field in self.required_fields:
            value = data.get(field)
            
            # Clean the value if it exists
            if value and isinstance(value, str):
                value = value.strip()
                if not value:
                    value = None
            
            validated_data[field] = value
        
        return validated_data
