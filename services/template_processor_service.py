"""
Template Processor Service for automatic field detection and marking in documents.
This service analyzes documents and identifies fields that need to be filled with company data.
"""

import json
import logging
import os
from typing import Dict, List, Tuple
from io import BytesIO

import google.generativeai as genai
from google.oauth2 import service_account
from docx import Document

logger = logging.getLogger(__name__)


class TemplateProcessorService:
    """
    Service for processing document templates and identifying fields for data insertion.
    """
    
    def __init__(self):
        """
        Initialize the TemplateProcessorService using Google Cloud authentication.
        """
        self._initialize_gemini()
        logger.info("TemplateProcessorService initialized successfully")
    
    def _initialize_gemini(self):
        """Initialize Google Gemini AI service using Google Cloud authentication"""
        try:
            # Get credentials file path
            credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if not credentials_path:
                logger.error("GOOGLE_APPLICATION_CREDENTIALS not set")
                raise ValueError("GOOGLE_APPLICATION_CREDENTIALS is required")
            
            if not os.path.exists(credentials_path):
                logger.error(f"Credentials file not found: {credentials_path}")
                raise FileNotFoundError(f"Credentials file not found: {credentials_path}")
            
            # Load service account credentials
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=['https://www.googleapis.com/auth/generative-language']
            )
            
            # Configure Gemini API with service account credentials
            genai.configure(credentials=credentials)
            
            # Initialize model (using flash model for better performance)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            logger.info("Gemini AI service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini AI service: {e}")
            raise
    
    async def analyze_text(self, text: str) -> Tuple[Dict[str, str], List[str]]:
        """
        Analyze text content and identify fields that need to be filled with company data.
        
        Args:
            text: Text content to analyze
            
        Returns:
            Tuple containing:
            - replacements: Dictionary mapping original text to text with placeholders
            - field_names: List of human-readable field names in Russian
        """
        try:
            if not text.strip():
                logger.warning("Text appears to be empty")
                return {}, []
            
            # Send request to Gemini
            prompt = self._create_analysis_prompt(text)
            
            logger.info("Sending text analysis request to Gemini...")
            response = await self._send_gemini_request(prompt)
            
            # Parse Gemini response
            field_data = self._parse_gemini_response(response)
            
            # Create replacements dictionary and field names list
            replacements = {}
            field_names = []
            
            for field in field_data:
                original_text = field.get('original_text', '')
                placeholder = field.get('placeholder', '')
                human_readable_name = field.get('human_readable_name', '')
                
                if original_text and placeholder:
                    # Store the mapping for later use
                    replacements[original_text] = placeholder
                    field_names.append(human_readable_name)
            
            logger.info(f"Text analysis completed. Found {len(field_data)} fields")
            return replacements, field_names
            
        except Exception as e:
            logger.error(f"Error analyzing text: {e}")
            return {}, []

    async def analyze_document(self, file_bytes: bytes) -> Tuple[Dict[str, str], List[str]]:
        """
        Analyze a document and identify fields that need to be filled with company data.
        
        Args:
            file_bytes: Document content as bytes
            
        Returns:
            Tuple containing:
            - replacements: Dictionary mapping original text to text with placeholders
            - field_names: List of human-readable field names in Russian
        """
        try:
            # Step 1: Extract text from document
            document_text = self._extract_text_from_docx(file_bytes)
            
            if not document_text.strip():
                logger.warning("Document appears to be empty or could not be read")
                return {}, []
            
            # Step 2: Send request to Gemini
            prompt = self._create_analysis_prompt(document_text)
            
            logger.info("Sending document analysis request to Gemini...")
            response = await self._send_gemini_request(prompt)
            
            # Step 3: Parse Gemini response
            field_data = self._parse_gemini_response(response)
            
            # Step 4: Create replacements dictionary and field names list
            replacements = {}
            field_names = []
            
            for field in field_data:
                original_text = field.get('original_text', '')
                placeholder = field.get('placeholder', '')
                human_readable_name = field.get('human_readable_name', '')
                
                if original_text and placeholder:
                    # Store the mapping for later use
                    replacements[original_text] = placeholder
                    field_names.append(human_readable_name)
            
            logger.info(f"Document analysis completed. Found {len(field_data)} fields")
            return replacements, field_names
            
        except Exception as e:
            logger.error(f"Error analyzing document: {e}")
            return {}, []
    
    def _extract_text_from_docx(self, file_bytes: bytes) -> str:
        """
        Extract text content from a DOCX file.
        
        Args:
            file_bytes: Document content as bytes
            
        Returns:
            Extracted text content
        """
        try:
            # Create BytesIO object from bytes
            doc_stream = BytesIO(file_bytes)
            
            # Load document
            doc = Document(doc_stream)
            
            # Extract text from all paragraphs
            text_parts = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text.strip())
            
            # Also extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            text_parts.append(cell.text.strip())
            
            full_text = '\n'.join(text_parts)
            logger.info(f"Extracted {len(full_text)} characters from document")
            return full_text
            
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {e}")
            return ""
    
    def _create_analysis_prompt(self, document_text: str) -> str:
        """
        Create a prompt for Gemini to analyze the document.
        
        Args:
            document_text: Text content of the document
            
        Returns:
            Formatted prompt for Gemini
        """
        prompt = f"""Ты — ассистент по подготовке шаблонов документов. Вот текст из документа:

{document_text}

Твоя задача — найти все места, куда нужно будет вставлять данные о компании-контрагенте. Это могут быть прочерки, пустые строки или фразы вроде '[Название компании]'.

Для каждого такого места придумай уникальный, короткий плейсхолдер на английском языке в формате `{{placeholder_name}}` (например, `{{company_name}}`, `{{inn}}`, `{{director_full_name}}`).

Также дай человекопонятное название для каждого поля на русском языке.

Верни результат в виде строгого JSON-массива объектов. Каждый объект должен иметь три ключа: `original_text` (фрагмент текста, который нужно заменить), `placeholder` (твой придуманный плейсхолдер) и `human_readable_name` (название поля на русском).

Пример: `[{{"original_text": "в лице Генерального директора ________________", "placeholder": "{{director_full_name}}", "human_readable_name": "ФИО генерального директора"}}]`

ВАЖНО: Отвечай ТОЛЬКО валидным JSON без дополнительных комментариев или объяснений."""
        
        return prompt
    
    async def _send_gemini_request(self, prompt: str) -> str:
        """
        Send request to Gemini API.
        
        Args:
            prompt: Prompt to send to Gemini
            
        Returns:
            Response from Gemini
        """
        try:
            # Generate content using Gemini
            response = self.model.generate_content(prompt)
            
            if response.text:
                logger.info("Received response from Gemini")
                return response.text
            else:
                logger.error("Empty response from Gemini")
                return ""
                
        except Exception as e:
            logger.error(f"Error sending request to Gemini: {e}")
            return ""
    
    def _parse_gemini_response(self, response: str) -> List[Dict[str, str]]:
        """
        Parse JSON response from Gemini.
        
        Args:
            response: Raw response from Gemini
            
        Returns:
            List of field data dictionaries
        """
        try:
            # Clean the response (remove markdown formatting if present)
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            # Parse JSON
            field_data = json.loads(cleaned_response)
            
            if not isinstance(field_data, list):
                logger.error("Gemini response is not a list")
                return []
            
            logger.info(f"Successfully parsed {len(field_data)} fields from Gemini response")
            return field_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response from Gemini: {e}")
            logger.error(f"Raw response: {response}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error parsing Gemini response: {e}")
            return []
