"""
Template Processor Service for automatic field detection and marking in documents.
This service analyzes documents and identifies fields that need to be filled with company data.
"""

import json
import logging
import os
import re
from typing import Dict, List, Tuple
from io import BytesIO

import google.generativeai as genai
from google.oauth2 import service_account
from docx import Document
from docx.shared import RGBColor
import docx2txt

logger = logging.getLogger(__name__)


class TemplateProcessorService:
    """
    Service for processing document templates using simplified analysis strategy.
    Analyzes documents and creates two files: preview for user and smart template for storage.
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
    
    async def analyze_and_prepare_templates(self, file_bytes: bytes, file_format: str = '.docx') -> Tuple[bytes, bytes]:
        """
        Analyze document and prepare two files: preview for user and smart template for storage.
        
        Args:
            file_bytes: Document content as bytes
            file_format: File format ('.docx' or '.doc')
            
        Returns:
            Tuple of (preview_bytes, smart_template_bytes)
        """
        try:
            print(f"📄 [ANALYZE] Начинаю анализ документа размером {len(file_bytes)} байт")
            
            # Step 1: Extract text from document
            if file_format == '.docx':
                print(f"📖 [ANALYZE] Извлекаю текст из DOCX файла...")
                document_text = self._extract_text_from_docx(file_bytes)
            elif file_format == '.doc':
                print(f"📖 [ANALYZE] Извлекаю текст из DOC файла...")
                document_text = self._extract_text_from_doc(file_bytes)
            else:
                print(f"❌ [ANALYZE] Неподдерживаемый формат файла: {file_format}")
                return b'', b''
            
            if not document_text.strip():
                print(f"⚠️ [ANALYZE] Документ пустой или не удалось прочитать")
                logger.warning("Document appears to be empty or could not be read")
                return b'', b''
            
            print(f"✅ [ANALYZE] Извлечено {len(document_text)} символов текста")
            
            # Step 2: Create simple prompt for Gemini
            prompt = self._create_simple_prompt(document_text)
            
            print(f"🤖 [ANALYZE] Отправляю запрос в Gemini...")
            logger.info("Sending document analysis request to Gemini...")
            response = await self._send_gemini_request(prompt)
            
            if not response:
                print(f"❌ [ANALYZE] Пустой ответ от Gemini")
                return b'', b''
            
            print(f"✅ [ANALYZE] Получен ответ от Gemini: {len(response)} символов")
            
            # Step 3: Parse JSON response
            replacements = self._parse_gemini_response(response)
            
            if not replacements:
                print(f"❌ [ANALYZE] Не удалось распарсить ответ Gemini")
                return b'', b''
            
            print(f"✅ [ANALYZE] Найдено {len(replacements)} полей для замены")
            
            # Step 4: Create preview file with red markers
            print(f"🔧 [ANALYZE] Создаю файл предпросмотра...")
            preview_bytes = self._create_preview_file(file_bytes, replacements)
            
            if not preview_bytes:
                print(f"❌ [ANALYZE] Не удалось создать файл предпросмотра")
                return b'', b''
            
            # Step 5: Create smart template with placeholders
            print(f"🔧 [ANALYZE] Создаю умный шаблон...")
            smart_template_bytes = self._create_smart_template(file_bytes, replacements)
            
            if not smart_template_bytes:
                print(f"❌ [ANALYZE] Не удалось создать умный шаблон")
                return b'', b''
            
            print(f"✅ [ANALYZE] Анализ завершен. Созданы файлы:")
            print(f"   - Предпросмотр: {len(preview_bytes)} байт")
            print(f"   - Умный шаблон: {len(smart_template_bytes)} байт")
            logger.info(f"Document analysis completed. Preview: {len(preview_bytes)} bytes, Smart template: {len(smart_template_bytes)} bytes")
            
            return preview_bytes, smart_template_bytes
            
        except Exception as e:
            print(f"❌ [ANALYZE] Ошибка при анализе документа: {e}")
            logger.error(f"Error in document analysis: {e}")
            return b'', b''
    
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
    
    def _extract_text_from_doc(self, file_bytes: bytes) -> str:
        """
        Extract text content from a DOC file.
        
        Args:
            file_bytes: Document content as bytes
            
        Returns:
            Extracted text content
        """
        try:
            # Create BytesIO object from bytes
            doc_stream = BytesIO(file_bytes)
            
            # Use docx2txt to extract text from DOC file
            text = docx2txt.process(doc_stream)
            
            if text:
                logger.info(f"Extracted {len(text)} characters from DOC document")
                return text
            else:
                logger.warning("No text extracted from DOC document")
                return ""
            
        except Exception as e:
            logger.error(f"Error extracting text from DOC: {e}")
            return ""
    
    def _create_simple_prompt(self, document_text: str) -> str:
        """
        Create simple prompt for Gemini to analyze the document.
        
        Args:
            document_text: Text content of the document
            
        Returns:
            Formatted prompt for Gemini
        """
        prompt = f"""Ты ассистент по документам. Вот текст договора: {document_text}

Найди два фрагмента текста:
1) место, где должно быть наименование контрагента (второй, незаполненной стороны)
2) место, где должен быть блок реквизитов этого контрагента

Верни JSON-массив с двумя объектами:
[{{"original_text": "...", "type": "NAME"}}, {{"original_text": "...", "type": "REQUISITES"}}]

Где:
- original_text - точный текст из документа, который нужно заменить
- type - либо "NAME" для наименования контрагента, либо "REQUISITES" для реквизитов

Если не можешь найти одно из полей, верни пустой массив []."""
        
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
            print(f"🚀 [GEMINI] Отправляю запрос в Gemini API...")
            # Generate content using Gemini
            response = self.model.generate_content(prompt)
            
            if response.text:
                print(f"✅ [GEMINI] Получен ответ от Gemini: {len(response.text)} символов")
                logger.info("Received response from Gemini")
                return response.text
            else:
                print(f"❌ [GEMINI] Пустой ответ от Gemini")
                logger.error("Empty response from Gemini")
                return ""
                
        except Exception as e:
            print(f"❌ [GEMINI] Ошибка при отправке запроса в Gemini: {e}")
            logger.error(f"Error sending request to Gemini: {e}")
            return ""
    
    def _create_preview_file(self, file_bytes: bytes, replacements: List[Dict[str, str]]) -> bytes:
        """
        Create preview file with red markers for user fields.
        
        Args:
            file_bytes: Original document bytes
            replacements: List of field replacements from Gemini
            
        Returns:
            Modified document bytes with red markers
        """
        try:
            print(f"🔧 [PREVIEW] Создаю файл предпросмотра...")
            
            # Create BytesIO object from input bytes
            doc_stream = BytesIO(file_bytes)
            
            # Load document using python-docx
            doc = Document(doc_stream)
            
            # Create replacement mapping for preview
            preview_replacements = {}
            for replacement in replacements:
                original_text = replacement['original_text']
                field_type = replacement['type']
                
                if field_type == 'NAME':
                    preview_replacements[original_text] = '[Наименование Контрагента]'
                elif field_type == 'REQUISITES':
                    preview_replacements[original_text] = '[Реквизиты Контрагента]'
            
            print(f"✅ [PREVIEW] Создано {len(preview_replacements)} замен для предпросмотра")
            
            # Apply replacements to document
            self._apply_replacements_to_document(doc, preview_replacements, is_preview=True)
            
            # Save modified document to memory
            output_stream = BytesIO()
            doc.save(output_stream)
            output_bytes = output_stream.getvalue()
            
            print(f"✅ [PREVIEW] Файл предпросмотра создан: {len(output_bytes)} байт")
            logger.info(f"Preview file created successfully. Output size: {len(output_bytes)} bytes")
            return output_bytes
            
        except Exception as e:
            print(f"❌ [PREVIEW] Ошибка при создании файла предпросмотра: {e}")
            logger.error(f"Error creating preview file: {e}")
            return b''
    
    def _create_smart_template(self, file_bytes: bytes, replacements: List[Dict[str, str]]) -> bytes:
        """
        Create smart template with standardized placeholders.
        
        Args:
            file_bytes: Original document bytes
            replacements: List of field replacements from Gemini
            
        Returns:
            Modified document bytes with smart placeholders
        """
        try:
            print(f"🔧 [SMART] Создаю умный шаблон...")
            
            # Create BytesIO object from input bytes
            doc_stream = BytesIO(file_bytes)
            
            # Load document using python-docx
            doc = Document(doc_stream)
            
            # Create replacement mapping for smart template
            smart_replacements = {}
            for replacement in replacements:
                original_text = replacement['original_text']
                field_type = replacement['type']
                
                if field_type == 'NAME':
                    smart_replacements[original_text] = '{{PARTY_2_NAME}}'
                elif field_type == 'REQUISITES':
                    smart_replacements[original_text] = '{{PARTY_2_REQUISITES}}'
            
            print(f"✅ [SMART] Создано {len(smart_replacements)} замен для умного шаблона")
            
            # Apply replacements to document
            self._apply_replacements_to_document(doc, smart_replacements, is_preview=False)
            
            # Save modified document to memory
            output_stream = BytesIO()
            doc.save(output_stream)
            output_bytes = output_stream.getvalue()
            
            print(f"✅ [SMART] Умный шаблон создан: {len(output_bytes)} байт")
            logger.info(f"Smart template created successfully. Output size: {len(output_bytes)} bytes")
            return output_bytes
            
        except Exception as e:
            print(f"❌ [SMART] Ошибка при создании умного шаблона: {e}")
            logger.error(f"Error creating smart template: {e}")
            return b''
    
    def _apply_replacements_to_document(self, doc: Document, replacements: Dict[str, str], is_preview: bool = True):
        """
        Apply replacements to document while preserving formatting.
        
        Args:
            doc: python-docx Document object
            replacements: Dictionary mapping original text to replacement text
            is_preview: Whether this is for preview (red formatting) or smart template
        """
        try:
            print(f"🔧 [APPLY] Применяю {len(replacements)} замен к документу...")
            
            # Process all paragraphs
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    self._apply_replacements_to_paragraph(paragraph, replacements, is_preview)
            
            # Process all tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            if paragraph.text.strip():
                                self._apply_replacements_to_paragraph(paragraph, replacements, is_preview)
            
            print(f"✅ [APPLY] Замены применены к документу")
            
        except Exception as e:
            print(f"❌ [APPLY] Ошибка при применении замен: {e}")
            logger.error(f"Error applying replacements to document: {e}")
    
    def _apply_replacements_to_paragraph(self, paragraph, replacements: Dict[str, str], is_preview: bool = True):
        """
        Apply replacements to paragraph while preserving formatting.
        
        Args:
            paragraph: python-docx paragraph object
            replacements: Dictionary mapping original text to replacement text
            is_preview: Whether this is for preview (red formatting) or smart template
        """
        try:
            original_text = paragraph.text
            
            # Check if this paragraph contains any replacement
            for original_part, replacement_text in replacements.items():
                if original_part.strip() and original_part in original_text:
                    # Clear the paragraph
                    paragraph.clear()
                    
                    # Split text around the original part
                    parts = original_text.split(original_part)
                    
                    # Add text before the field
                    if parts[0]:
                        paragraph.add_run(parts[0])
                    
                    # Add replacement text with formatting
                    replacement_run = paragraph.add_run(replacement_text)
                    if is_preview:
                        # Red formatting for preview
                        replacement_run.font.color.rgb = RGBColor(255, 0, 0)  # Red color
                        replacement_run.font.bold = True
                    
                    # Add text after the field
                    if len(parts) > 1 and parts[1]:
                        paragraph.add_run(parts[1])
                    
                    print(f"✅ [REPLACE] Применена замена: '{original_part[:30]}...' -> '{replacement_text}'")
                    break
            
        except Exception as e:
            print(f"❌ [REPLACE] Ошибка при применении замены: {e}")
            logger.error(f"Error applying replacement to paragraph: {e}")
    
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

            # Validate that each item has required fields
            valid_fields = []
            for item in field_data:
                if isinstance(item, dict) and 'original_text' in item and 'type' in item:
                    if item['type'] in ['NAME', 'REQUISITES']:
                        valid_fields.append(item)
                        print(f"✅ [PARSE] Найдено поле: {item['type']} -> '{item['original_text'][:50]}...'")
                    else:
                        print(f"⚠️ [PARSE] Неизвестный тип поля: {item['type']}")
                else:
                    print(f"⚠️ [PARSE] Некорректный формат поля: {item}")
            
            logger.info(f"Successfully parsed {len(valid_fields)} valid fields from Gemini response")
            return valid_fields

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response from Gemini: {e}")
            logger.error(f"Raw response: {response}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error parsing Gemini response: {e}")
            return []