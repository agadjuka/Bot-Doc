"""
Template Processor Service for automatic field detection and marking in documents.
This service analyzes documents and identifies fields that need to be filled with company data.
"""

import json
import logging
import os
import re
import tempfile
from typing import Dict, List, Tuple
from io import BytesIO

import google.generativeai as genai
from google.oauth2 import service_account
from docx import Document
from docx.shared import RGBColor
import docx2txt
from docx2markdown._docx_to_markdown import docx_to_markdown

from config.prompts import PromptManager

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
        self.prompt_manager = PromptManager()
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
            print(f"🔍 [ANALYZE] Начинаю парсинг ответа Gemini...")
            replacements = self._parse_gemini_response(response)
            
            if not replacements:
                print(f"❌ [ANALYZE] Не удалось распарсить ответ Gemini")
                print(f"❌ [ANALYZE] Ответ Gemini: {response[:300]}...")
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
            print(f"❌ [ANALYZE] Тип ошибки: {type(e).__name__}")
            import traceback
            print(f"❌ [ANALYZE] Полный traceback:")
            traceback.print_exc()
            logger.error(f"Error in document analysis: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return b'', b''
    
    def _extract_text_from_docx(self, file_bytes: bytes) -> str:
        """
        Extract text content from a DOCX file and convert to Markdown format.
        
        Args:
            file_bytes: Document content as bytes
            
        Returns:
            Extracted text content in Markdown format
        """
        try:
            # Create temporary files for input and output
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_docx:
                temp_docx.write(file_bytes)
                temp_docx_path = temp_docx.name
            
            with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as temp_md:
                temp_md_path = temp_md.name
            
            try:
                # Convert DOCX to Markdown using docx2markdown
                docx_to_markdown(temp_docx_path, temp_md_path)
                
                # Read the generated markdown file
                with open(temp_md_path, 'r', encoding='utf-8') as md_file:
                    markdown_text = md_file.read()
                
                if markdown_text:
                    logger.info(f"Extracted {len(markdown_text)} characters from document in Markdown format")
                    return markdown_text
                else:
                    logger.warning("No text extracted from DOCX document")
                    return ""
                    
            finally:
                # Clean up temporary files
                try:
                    os.unlink(temp_docx_path)
                    os.unlink(temp_md_path)
                except OSError:
                    pass
            
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
        Create comprehensive prompt for Gemini to analyze the document.
        
        Args:
            document_text: Text content of the document
            
        Returns:
            Formatted prompt for Gemini
        """
        prompt = self.prompt_manager.get_document_analysis_prompt(document_text)
        print(f"🔍 [PROMPT] Создан промпт длиной {len(prompt)} символов")
        print(f"🔍 [PROMPT] Первые 200 символов промпта: {prompt[:200]}")
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
                print(f"🔍 [GEMINI] Первые 200 символов ответа: {response.text[:200]}")
                print(f"🔍 [GEMINI] Полный ответ от Gemini:")
                print(f"🔍 [GEMINI] {response.text}")
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
            print(f"🔍 [PREVIEW] Получено {len(replacements)} замен от Gemini:")
            for i, replacement in enumerate(replacements):
                print(f"🔍 [PREVIEW] Замена {i+1}: type='{replacement['type']}', text='{replacement['original_text'][:50]}...'")
            
            for replacement in replacements:
                original_text = replacement['original_text']
                field_type = replacement['type']
                
                print(f"🔍 [PREVIEW] Обрабатываю замену: type='{field_type}', text='{original_text[:50]}...'")
                
                if field_type == 'PARTY_2_NAME':
                    preview_replacements[original_text] = '[Наименование Контрагента]'
                    print(f"✅ [PREVIEW] Создана замена PARTY_2_NAME: '{original_text[:30]}...' -> '[Наименование Контрагента]'")
                elif field_type == 'PARTY_2_REQUISITES':
                    # Для реквизитов заменяем каждую строку блока отдельно,
                    # чтобы корректно попасть в соответствующие параграфы
                    lines = [l for l in original_text.split('\n') if l.strip()]
                    for ln in lines:
                        preview_replacements[ln] = '[Реквизиты Контрагента]'
                        print(f"✅ [PREVIEW] Создана замена PARTY_2_REQUISITES: '{ln[:30]}...' -> '[Реквизиты Контрагента]'")
                elif field_type == 'PARTY_2_DIRECTOR_NAME':
                    preview_replacements[original_text] = '[Имя Директора]'
                    print(f"✅ [PREVIEW] Создана замена PARTY_2_DIRECTOR_NAME: '{original_text[:30]}...' -> '[Имя Директора]'")
                else:
                    print(f"⚠️ [PREVIEW] Неизвестный тип поля: '{field_type}'")
            
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
            print(f"🔍 [SMART] Получено {len(replacements)} замен от Gemini:")
            for i, replacement in enumerate(replacements):
                print(f"🔍 [SMART] Замена {i+1}: type='{replacement['type']}', text='{replacement['original_text'][:50]}...'")
            
            # Create BytesIO object from input bytes
            doc_stream = BytesIO(file_bytes)
            
            # Load document using python-docx
            doc = Document(doc_stream)
            
            # Create replacement mapping for smart template
            smart_replacements = {}
            for replacement in replacements:
                original_text = replacement['original_text']
                field_type = replacement['type']
                
                print(f"🔍 [SMART] Обрабатываю замену: type='{field_type}', text='{original_text[:50]}...'")
                
                if field_type == 'PARTY_2_NAME':
                    smart_replacements[original_text] = '{{PARTY_2_NAME}}'
                    print(f"✅ [SMART] Создана замена PARTY_2_NAME: '{original_text[:30]}...' -> '{{PARTY_2_NAME}}'")
                elif field_type == 'PARTY_2_REQUISITES':
                    # Для реквизитов заменяем каждую строку блока отдельно на плейсхолдер реквизитов
                    lines = [l for l in original_text.split('\n') if l.strip()]
                    for ln in lines:
                        smart_replacements[ln] = '{{PARTY_2_REQUISITES}}'
                        print(f"✅ [SMART] Создана замена PARTY_2_REQUISITES: '{ln[:30]}...' -> '{{PARTY_2_REQUISITES}}'")
                elif field_type == 'PARTY_2_DIRECTOR_NAME':
                    smart_replacements[original_text] = '{{PARTY_2_DIRECTOR_NAME}}'
                    print(f"✅ [SMART] Создана замена PARTY_2_DIRECTOR_NAME: '{original_text[:30]}...' -> '{{PARTY_2_DIRECTOR_NAME}}'")
                else:
                    print(f"⚠️ [SMART] Неизвестный тип поля: '{field_type}'")
            
            print(f"✅ [SMART] Создано {len(smart_replacements)} замен для умного шаблона")
            print(f"🔍 [SMART] Итоговые замены:")
            for original, replacement in smart_replacements.items():
                print(f"🔍 [SMART] '{original[:30]}...' -> '{replacement}'")
            
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
            
            # Check if this paragraph contains any replacement (строгое совпадение для строк подчеркиваний)
            for original_part, replacement_text in replacements.items():
                if not original_part.strip():
                    continue
                # Для линий из подчеркиваний и пробелов требуем точного совпадения,
                # чтобы короткие линии (директор) не заменяли длинные (реквизиты)
                is_underscore_only = bool(re.fullmatch(r"[_\s]+", original_part))
                match = (original_text == original_part) if is_underscore_only else (original_part in original_text)
                if match:
                    print(f"🔍 [REPLACE] Найдено совпадение в параграфе:")
                    print(f"🔍 [REPLACE] Исходный текст параграфа: '{original_text[:100]}...'")
                    print(f"🔍 [REPLACE] Ищем: '{original_part[:50]}...'")
                    print(f"🔍 [REPLACE] Заменяем на: '{replacement_text}'")
                    print(f"🔍 [REPLACE] Тип файла: {'предпросмотр' if is_preview else 'умный шаблон'}")
                    
                    # Clear the paragraph
                    paragraph.clear()
                    
                    # Split text around the original part
                    parts = ["", ""] if original_text == original_part else original_text.split(original_part)
                    
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
            print(f"🔍 [PARSE] Начинаю парсинг ответа от Gemini...")
            print(f"🔍 [PARSE] Длина ответа: {len(response)} символов")
            print(f"🔍 [PARSE] Первые 200 символов ответа: {response[:200]}")
            
            # Clean the response (remove markdown formatting if present)
            cleaned_response = response.strip()
            
            # Remove markdown code blocks
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]
            
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            
            cleaned_response = cleaned_response.strip()
            
            print(f"🔍 [PARSE] Очищенный ответ: {cleaned_response[:100]}...")
            
            # Try multiple parsing strategies
            field_data = None
            
            # Strategy 1: Try to find JSON array in the response
            json_start = cleaned_response.find('[')
            json_end = cleaned_response.rfind(']') + 1
            
            if json_start != -1 and json_end > json_start:
                json_text = cleaned_response[json_start:json_end]
                print(f"🔍 [PARSE] Найден JSON массив: позиция {json_start} - {json_end}")
                print(f"🔍 [PARSE] JSON текст: {json_text[:200]}...")
                try:
                    field_data = json.loads(json_text)
                    print(f"✅ [PARSE] Успешно распарсен JSON массив")
                except json.JSONDecodeError as e:
                    print(f"❌ [PARSE] Ошибка парсинга JSON массива: {e}")
                    field_data = None
            
            # Strategy 2: Try to parse the whole response
            if field_data is None:
                try:
                    field_data = json.loads(cleaned_response)
                    print(f"✅ [PARSE] Успешно распарсен весь ответ")
                except json.JSONDecodeError as e:
                    print(f"❌ [PARSE] Ошибка парсинга всего ответа: {e}")
                    field_data = None
            
            # Strategy 3: Try to extract JSON using regex
            if field_data is None:
                json_pattern = r'\[.*?\]'
                json_matches = re.findall(json_pattern, cleaned_response, re.DOTALL)
                if json_matches:
                    for json_match in json_matches:
                        try:
                            field_data = json.loads(json_match)
                            print(f"✅ [PARSE] Успешно распарсен JSON через regex")
                            break
                        except json.JSONDecodeError:
                            continue
            
            if field_data is None:
                print(f"❌ [PARSE] Не удалось распарсить JSON из ответа")
                logger.error("Could not parse JSON from Gemini response")
                return []

            if not isinstance(field_data, list):
                logger.error("Gemini response is not a list")
                print(f"❌ [PARSE] Ответ не является массивом: {type(field_data)}")
                return []

            # Validate that each item has required fields
            valid_fields = []
            for i, item in enumerate(field_data):
                print(f"🔍 [PARSE] Проверяю элемент {i}: {item}")
                if isinstance(item, dict) and 'original_text' in item and 'type' in item:
                    if item['type'] in ['PARTY_2_NAME', 'PARTY_2_REQUISITES', 'PARTY_2_DIRECTOR_NAME']:
                        valid_fields.append(item)
                        print(f"✅ [PARSE] Найдено поле: {item['type']} -> '{item['original_text'][:50]}...'")
                        print(f"🔍 [PARSE] Полный текст поля: '{item['original_text']}'")
                    else:
                        print(f"⚠️ [PARSE] Неизвестный тип поля: {item['type']}")
                else:
                    print(f"⚠️ [PARSE] Некорректный формат поля: {item}")
            
            print(f"🔍 [PARSE] Итоговый список валидных полей:")
            for i, field in enumerate(valid_fields):
                print(f"🔍 [PARSE] Поле {i+1}: type='{field['type']}', text='{field['original_text'][:100]}...'")
            
            logger.info(f"Successfully parsed {len(valid_fields)} valid fields from Gemini response")
            return valid_fields

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response from Gemini: {e}")
            logger.error(f"Raw response: {response}")
            print(f"❌ [PARSE] Ошибка парсинга JSON: {e}")
            print(f"❌ [PARSE] Исходный ответ: {response[:500]}...")
            return []
        except Exception as e:
            logger.error(f"Unexpected error parsing Gemini response: {e}")
            print(f"❌ [PARSE] Неожиданная ошибка: {e}")
            return []