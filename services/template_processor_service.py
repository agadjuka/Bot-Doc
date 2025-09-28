"""
Template Processor Service for automatic field detection and marking in documents.
This service analyzes documents and identifies fields that need to be filled with company data.
"""

import json
import logging
import os
import re
import tempfile
import io
import copy
from typing import Dict, List, Tuple
from io import BytesIO

import google.generativeai as genai
from google.oauth2 import service_account
from docx import Document
from docx.shared import RGBColor
from docx.oxml.shared import qn
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
    
    def _remove_highlighting(self, run):
        """
        Remove yellow highlighting from a run by clearing background color.
        
        Args:
            run: python-docx run object
        """
        try:
            # Remove highlighting by clearing the highlight property
            if hasattr(run, '_element'):
                # Remove w:highlight attribute if it exists
                if run._element.get(qn('w:highlight')):
                    del run._element.attrib[qn('w:highlight')]
                
                # Remove w:shd (shading) attribute if it exists
                if run._element.get(qn('w:shd')):
                    del run._element.attrib[qn('w:shd')]
                
                # Also check for highlighting in the run's properties
                run_props = run._element.find(qn('w:rPr'))
                if run_props is not None:
                    highlight_elem = run_props.find(qn('w:highlight'))
                    if highlight_elem is not None:
                        run_props.remove(highlight_elem)
                    
                    shading_elem = run_props.find(qn('w:shd'))
                    if shading_elem is not None:
                        run_props.remove(shading_elem)
                
                # Additional cleanup for any background color formatting
                # Remove any w:color with background color
                color_elem = run_props.find(qn('w:color')) if run_props is not None else None
                if color_elem is not None:
                    # Check if it's a background color (usually has w:val="auto" or specific color)
                    if color_elem.get(qn('w:val')) in ['auto', 'yellow', 'FFFF00']:
                        run_props.remove(color_elem)
            
            # Also try to remove highlighting using python-docx properties
            if hasattr(run, 'font') and hasattr(run.font, 'highlight_color'):
                try:
                    run.font.highlight_color = None
                except:
                    pass
            
            print(f"✅ [HIGHLIGHT] Удалена желтая заливка из run: '{run.text[:50]}...'")
            
        except Exception as e:
            print(f"⚠️ [HIGHLIGHT] Ошибка при удалении заливки: {e}")
            # Не критично, продолжаем работу

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
    
    def _index_runs_and_build_map(self, doc_object: Document) -> Tuple[str, Dict[str, any]]:
        """
        Create detailed indexing of document at run level for precise analysis.
        
        Args:
            doc_object: python-docx Document object
            
        Returns:
            Tuple of (map_for_gemini, coords_dictionary)
            - map_for_gemini: Text map of document with run IDs for AI analysis
            - coords_dictionary: Python dictionary for quick navigation by run IDs
        """
        try:
            print(f"🔍 [INDEX] Начинаю детальную индексацию документа на уровне run-ов...")
            
            # Initialize variables
            map_for_gemini = ""
            coords_dictionary = {}
            run_counter = 0
            
            # Process all paragraphs
            for paragraph in doc_object.paragraphs:
                for run in paragraph.runs:
                    # Generate unique ID for this run
                    run_id = f"run-{run_counter}"
                    
                    # Add run to coordinates dictionary (save direct reference to object)
                    coords_dictionary[run_id] = run
                    
                    # Add run to map for Gemini
                    map_for_gemini += f"[{run_id}]{run.text}"
                    
                    # Increment counter
                    run_counter += 1
                
                # Add newline after each paragraph to preserve structure
                map_for_gemini += "\n"
            
            # Process all tables
            for table in doc_object.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            for run in paragraph.runs:
                                # Generate unique ID for this run
                                run_id = f"run-{run_counter}"
                                
                                # Add run to coordinates dictionary
                                coords_dictionary[run_id] = run
                                
                                # Add run to map for Gemini
                                map_for_gemini += f"[{run_id}]{run.text}"
                                
                                # Increment counter
                                run_counter += 1
                            
                            # Add newline after each paragraph in table cells
                            map_for_gemini += "\n"
            
            print(f"✅ [INDEX] Индексация завершена:")
            print(f"   - Создано {len(coords_dictionary)} run-ов")
            print(f"   - Размер карты для Gemini: {len(map_for_gemini)} символов")
            print(f"   - Первые 200 символов карты: {map_for_gemini[:200]}...")
            
            return map_for_gemini, coords_dictionary
            
        except Exception as e:
            print(f"❌ [INDEX] Ошибка при индексации документа: {e}")
            logger.error(f"Error indexing document runs: {e}")
            return "", {}
    
    def _sync_docs_with_map(self, doc_object: Document, coords_dictionary: Dict[str, any], modified_map: str) -> Tuple[bytes, bytes]:
        """
        Synchronize documents with the modified map from Gemini.
        This method replaces the old surgical approach with simple text synchronization.
        
        Args:
            doc_object: Original Document object
            coords_dictionary: Dictionary mapping run_id to run objects
            modified_map: Modified text map from Gemini with run markers
            
        Returns:
            Tuple of (preview_bytes, smart_template_bytes)
        """
        try:
            print(f"🔄 [SYNC] Начинаю синхронизацию документов с картой...")
            print(f"🔄 [SYNC] Размер модифицированной карты: {len(modified_map)} символов")
            print(f"🔄 [SYNC] Первые 200 символов карты: {modified_map[:200]}...")
            
            # Step 1: Create completely independent copies of the original document
            print(f"📋 [SYNC] Создаю полностью независимые копии документа...")
            
            # Сохраняем оригинальный документ в байты и загружаем заново для каждой копии
            original_bytes = BytesIO()
            doc_object.save(original_bytes)
            original_bytes.seek(0)
            
            # Создаем preview документ из байтов
            preview_doc = Document(original_bytes)
            original_bytes.seek(0)
            
            # Создаем smart template документ из байтов
            smart_template_doc = Document(original_bytes)
            
            print(f"✅ [SYNC] Созданы две полностью независимые копии документа")
            
            # Step 2: Rebuild coordinates dictionary for both copies
            print(f"🔍 [SYNC] Перестраиваю словари координат для копий...")
            _, preview_coords_dictionary = self._index_runs_and_build_map(preview_doc)
            _, smart_template_coords_dictionary = self._index_runs_and_build_map(smart_template_doc)
            print(f"✅ [SYNC] Словари координат перестроены:")
            print(f"   - Preview: {len(preview_coords_dictionary)} run-ов")
            print(f"   - Smart template: {len(smart_template_coords_dictionary)} run-ов")
            
            # Step 3: Parse the modified map to extract run_id and new_text pairs
            print(f"🔍 [SYNC] Парсинг модифицированной карты...")
            sync_plan = self._parse_modified_map(modified_map)
            print(f"✅ [SYNC] Извлечено {len(sync_plan)} пар для синхронизации")
            
            # Step 4: Apply synchronization to both documents
            print(f"🔄 [SYNC] Применяю синхронизацию к документам...")
            
            for run_id, new_text in sync_plan.items():
                print(f"🔄 [SYNC] Синхронизирую {run_id}: '{new_text[:50]}...'")
                
                # Find target runs in both documents
                preview_run = preview_coords_dictionary.get(run_id)
                smart_template_run = smart_template_coords_dictionary.get(run_id)
                
                if not preview_run:
                    print(f"⚠️ [SYNC] Run {run_id} не найден в preview документе")
                    continue
                    
                if not smart_template_run:
                    print(f"⚠️ [SYNC] Run {run_id} не найден в smart template документе")
                    continue
                
                # Synchronize text in both documents
                preview_run.text = new_text
                smart_template_run.text = new_text
                
                print(f"✅ [SYNC] Синхронизирован {run_id}")
            
            print(f"✅ [SYNC] Синхронизация текста завершена")
            
            # Step 5: Post-processing - Apply styles and placeholders
            print(f"🎨 [SYNC] Применяю стили и плейсхолдеры...")
            
            # Process preview document - apply red bold style to runs with markers
            for run_id, run in preview_coords_dictionary.items():
                if '[' in run.text and ']' in run.text:
                    # Remove highlighting first
                    self._remove_highlighting(run)
                    # Apply red bold style
                    run.font.color.rgb = RGBColor(255, 0, 0)
                    run.bold = True
                    print(f"🎨 [SYNC] Применен стиль к preview run {run_id}: '{run.text}'")
            
            # Process smart template document - convert markers to placeholders
            for run_id, run in smart_template_coords_dictionary.items():
                if '[' in run.text and ']' in run.text:
                    # Convert [field] to {{field}}
                    new_text = run.text.replace('[', '{{').replace(']', '}}')
                    run.text = new_text
                    print(f"🔧 [SYNC] Конвертирован плейсхолдер в smart template run {run_id}: '{new_text}'")
            
            print(f"✅ [SYNC] Стили и плейсхолдеры применены")
            
            # Step 6: Save both documents to bytes
            print(f"💾 [SYNC] Сохраняю документы в байты...")
            
            # Save preview document
            preview_stream = BytesIO()
            preview_doc.save(preview_stream)
            preview_bytes = preview_stream.getvalue()
            print(f"✅ [SYNC] Preview документ сохранен: {len(preview_bytes)} байт")
            
            # Save smart template document
            smart_template_stream = BytesIO()
            smart_template_doc.save(smart_template_stream)
            smart_template_bytes = smart_template_stream.getvalue()
            print(f"✅ [SYNC] Smart template документ сохранен: {len(smart_template_bytes)} байт")
            
            print(f"🎉 [SYNC] Синхронизация документов завершена успешно!")
            return preview_bytes, smart_template_bytes
            
        except Exception as e:
            print(f"❌ [SYNC] Ошибка при синхронизации документов: {e}")
            logger.error(f"Error in document synchronization: {e}")
            import traceback
            traceback.print_exc()
            return b'', b''
    
    def _parse_modified_map(self, modified_map: str) -> Dict[str, str]:
        """
        Parse the modified map from Gemini to extract run_id and new_text pairs.
        
        Args:
            modified_map: Modified text map with run markers from Gemini
            
        Returns:
            Dictionary mapping run_id to new_text
        """
        try:
            print(f"🔍 [PARSE] Парсинг модифицированной карты...")
            
            # Use regex to find all [run-ID]text patterns
            pattern = r'\[(run-\d+)\]([^\[]*)'
            matches = re.findall(pattern, modified_map)
            
            sync_plan = {}
            for run_id, new_text in matches:
                # Clean up the text (remove extra whitespace)
                cleaned_text = new_text.strip()
                sync_plan[run_id] = cleaned_text
                print(f"🔍 [PARSE] Найдена пара: {run_id} -> '{cleaned_text[:50]}...'")
            
            print(f"✅ [PARSE] Извлечено {len(sync_plan)} пар из карты")
            return sync_plan
            
        except Exception as e:
            print(f"❌ [PARSE] Ошибка при парсинге карты: {e}")
            logger.error(f"Error parsing modified map: {e}")
            return {}
    
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
            
            # Step 1: Load document using python-docx for precise run-level analysis
            if file_format == '.docx':
                print(f"📖 [ANALYZE] Загружаю DOCX документ для детального анализа...")
                doc_object = Document(io.BytesIO(file_bytes))
            elif file_format == '.doc':
                print(f"❌ [ANALYZE] DOC формат не поддерживается для детального анализа")
                return b'', b''
            else:
                print(f"❌ [ANALYZE] Неподдерживаемый формат файла: {file_format}")
                return b'', b''
            
            # Step 2: Create detailed run-level indexing
            print(f"🔍 [ANALYZE] Создаю детальную индексацию на уровне run-ов...")
            map_for_gemini, coords_dictionary = self._index_runs_and_build_map(doc_object)
            
            if not map_for_gemini.strip():
                print(f"⚠️ [ANALYZE] Документ пустой или не удалось проиндексировать")
                logger.warning("Document appears to be empty or could not be indexed")
                return b'', b''
            
            print(f"✅ [ANALYZE] Индексация завершена:")
            print(f"   - Создано {len(coords_dictionary)} run-ов")
            print(f"   - Размер карты для Gemini: {len(map_for_gemini)} символов")
            print(f"   - Первые 500 символов карты: {map_for_gemini[:500]}...")
            
            # Step 3: Call Gemini for document analysis
            print(f"🤖 [GEMINI] Отправляю карту документа в Gemini для анализа...")
            prompt = self.prompt_manager.get_document_analysis_prompt(map_for_gemini)
            print(f"🔍 [GEMINI] Создан промпт длиной {len(prompt)} символов")
            
            # Send request to Gemini
            gemini_response = await self._send_gemini_request(prompt)
            
            if not gemini_response:
                print(f"❌ [GEMINI] Пустой ответ от Gemini")
                logger.error("Empty response from Gemini")
                return b'', b''
            
            print(f"✅ [GEMINI] Получен ответ от Gemini: {len(gemini_response)} символов")
            print(f"🔍 [GEMINI] Первые 200 символов ответа: {gemini_response[:200]}...")
            logger.debug(f"Получен ответ от Gemini: {gemini_response}")
            
            # Step 4: Synchronize documents with modified map
            print(f"🔄 [ANALYZE] Синхронизирую документы с модифицированной картой...")
            preview_bytes, smart_template_bytes = self._sync_docs_with_map(doc_object, coords_dictionary, gemini_response)
            
            if not preview_bytes or not smart_template_bytes:
                print(f"❌ [ANALYZE] Ошибка при синхронизации документов")
                logger.error("Failed to synchronize documents with modified map")
                return b'', b''
            
            print(f"✅ [ANALYZE] Синхронизация документов завершена успешно:")
            print(f"   - Preview файл: {len(preview_bytes)} байт")
            print(f"   - Smart template файл: {len(smart_template_bytes)} байт")
            
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
            
            # Create replacement mapping for preview with unique keys
            preview_replacements = {}
            field_counters = {'PARTY_2_NAME': 0, 'PARTY_2_REQUISITES': 0, 'PARTY_2_DIRECTOR_NAME': 0}
            print(f"🔍 [PREVIEW] Получено {len(replacements)} замен от Gemini:")
            for i, replacement in enumerate(replacements):
                print(f"🔍 [PREVIEW] Замена {i+1}: type='{replacement['type']}', text='{replacement['original_text'][:50]}...'")
            
            for replacement in replacements:
                original_text = replacement['original_text']
                field_type = replacement['type']
                
                print(f"🔍 [PREVIEW] Обрабатываю замену: type='{field_type}', text='{original_text[:50]}...'")
                
                if field_type == 'PARTY_2_NAME':
                    field_counters['PARTY_2_NAME'] += 1
                    unique_key = f"{original_text}_{field_counters['PARTY_2_NAME']}"
                    preview_replacements[unique_key] = {
                        'original_text': original_text,
                        'replacement': '[Наименование Контрагента]'
                    }
                    print(f"✅ [PREVIEW] Создана замена PARTY_2_NAME: '{original_text[:30]}...' -> '[Наименование Контрагента]'")
                elif field_type == 'PARTY_2_REQUISITES':
                    field_counters['PARTY_2_REQUISITES'] += 1
                    # Для реквизитов заменяем каждую строку блока отдельно,
                    # чтобы корректно попасть в соответствующие параграфы
                    lines = [l for l in original_text.split('\n') if l.strip()]
                    for i, ln in enumerate(lines):
                        unique_key = f"{ln}_{field_counters['PARTY_2_REQUISITES']}_{i}"
                        preview_replacements[unique_key] = {
                            'original_text': ln,
                            'replacement': '[Реквизиты Контрагента]'
                        }
                        print(f"✅ [PREVIEW] Создана замена PARTY_2_REQUISITES: '{ln[:30]}...' -> '[Реквизиты Контрагента]'")
                elif field_type == 'PARTY_2_DIRECTOR_NAME':
                    field_counters['PARTY_2_DIRECTOR_NAME'] += 1
                    unique_key = f"{original_text}_{field_counters['PARTY_2_DIRECTOR_NAME']}"
                    preview_replacements[unique_key] = {
                        'original_text': original_text,
                        'replacement': '[Имя Директора]'
                    }
                    print(f"✅ [PREVIEW] Создана замена PARTY_2_DIRECTOR_NAME: '{original_text[:30]}...' -> '[Имя Директора]'")
                else:
                    print(f"⚠️ [PREVIEW] Неизвестный тип поля: '{field_type}'")
            
            print(f"✅ [PREVIEW] Создано {len(preview_replacements)} замен для предпросмотра")
            
            # Apply replacements to document with order preservation
            self._apply_replacements_to_document_ordered(doc, preview_replacements, is_preview=True)
            
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
            field_counters = {'PARTY_2_NAME': 0, 'PARTY_2_REQUISITES': 0, 'PARTY_2_DIRECTOR_NAME': 0}
            
            for replacement in replacements:
                original_text = replacement['original_text']
                field_type = replacement['type']
                
                print(f"🔍 [SMART] Обрабатываю замену: type='{field_type}', text='{original_text[:50]}...'")
                
                if field_type == 'PARTY_2_NAME':
                    field_counters['PARTY_2_NAME'] += 1
                    # Создаем уникальный ключ для каждой замены
                    unique_key = f"{original_text}_{field_counters['PARTY_2_NAME']}"
                    smart_replacements[unique_key] = {
                        'original_text': original_text,
                        'replacement': '{{PARTY_2_NAME}}'
                    }
                    print(f"✅ [SMART] Создана замена PARTY_2_NAME: '{original_text[:30]}...' -> '{{PARTY_2_NAME}}'")
                elif field_type == 'PARTY_2_REQUISITES':
                    field_counters['PARTY_2_REQUISITES'] += 1
                    # Для реквизитов заменяем каждую строку блока отдельно на плейсхолдер реквизитов
                    lines = [l for l in original_text.split('\n') if l.strip()]
                    for i, ln in enumerate(lines):
                        unique_key = f"{ln}_{field_counters['PARTY_2_REQUISITES']}_{i}"
                        smart_replacements[unique_key] = {
                            'original_text': ln,
                            'replacement': '{{PARTY_2_REQUISITES}}'
                        }
                        print(f"✅ [SMART] Создана замена PARTY_2_REQUISITES: '{ln[:30]}...' -> '{{PARTY_2_REQUISITES}}'")
                elif field_type == 'PARTY_2_DIRECTOR_NAME':
                    field_counters['PARTY_2_DIRECTOR_NAME'] += 1
                    # Создаем уникальный ключ для каждой замены
                    unique_key = f"{original_text}_{field_counters['PARTY_2_DIRECTOR_NAME']}"
                    smart_replacements[unique_key] = {
                        'original_text': original_text,
                        'replacement': '{{PARTY_2_DIRECTOR_NAME}}'
                    }
                    print(f"✅ [SMART] Создана замена PARTY_2_DIRECTOR_NAME: '{original_text[:30]}...' -> '{{PARTY_2_DIRECTOR_NAME}}'")
                else:
                    print(f"⚠️ [SMART] Неизвестный тип поля: '{field_type}'")
            
            print(f"✅ [SMART] Создано {len(smart_replacements)} замен для умного шаблона")
            print(f"🔍 [SMART] Итоговые замены:")
            for original, replacement in smart_replacements.items():
                print(f"🔍 [SMART] '{original[:30]}...' -> '{replacement}'")
            
            # Apply replacements to document with order preservation
            self._apply_replacements_to_document_ordered(doc, smart_replacements, is_preview=False)
            
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
    
    def _apply_replacements_to_document_ordered(self, doc: Document, smart_replacements: Dict[str, Dict], is_preview: bool = True):
        """
        Apply replacements to document with order preservation for identical text.
        
        Args:
            doc: python-docx Document object
            smart_replacements: Dictionary with unique keys and replacement data
            is_preview: Whether this is for preview (red formatting) or smart template
        """
        try:
            print(f"🔧 [APPLY] Применяю {len(smart_replacements)} замен к документу с сохранением порядка...")
            
            # Convert to list of replacements with order
            replacements_list = []
            for key, data in smart_replacements.items():
                replacements_list.append({
                    'original_text': data['original_text'],
                    'replacement': data['replacement']
                })
            
            # Process all paragraphs
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    self._apply_replacements_to_paragraph_ordered(paragraph, replacements_list, is_preview)
            
            # Process all tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            if paragraph.text.strip():
                                self._apply_replacements_to_paragraph_ordered(paragraph, replacements_list, is_preview)
            
            print(f"✅ [APPLY] Замены применены к документу с сохранением порядка")
            
        except Exception as e:
            print(f"❌ [APPLY] Ошибка при применении замен с сохранением порядка: {e}")
            logger.error(f"Error applying ordered replacements to document: {e}")
    
    def _apply_replacements_to_paragraph_ordered(self, paragraph, replacements_list: List[Dict], is_preview: bool = True):
        """
        Apply replacements to paragraph with order preservation.
        
        Args:
            paragraph: python-docx paragraph object
            replacements_list: List of replacement dictionaries
            is_preview: Whether this is for preview (red formatting) or smart template
        """
        try:
            original_text = paragraph.text
            
            # Apply replacements in order, but only once per occurrence
            applied_replacements = set()
            
            for replacement in replacements_list:
                original_part = replacement['original_text']
                replacement_text = replacement['replacement']
                
                if not original_part.strip():
                    continue
                
                # Check if this paragraph contains the replacement text
                if original_part in original_text:
                    # Create a unique identifier for this replacement
                    replacement_id = f"{original_part}_{original_text.find(original_part)}"
                    
                    if replacement_id not in applied_replacements:
                        # Apply the replacement
                        new_text = original_text.replace(original_part, replacement_text, 1)  # Replace only first occurrence
                        if new_text != original_text:
                            print(f"🔍 [REPLACE] Найдено совпадение в параграфе:")
                            print(f"🔍 [REPLACE] Исходный текст параграфа: '{original_text[:50]}...'")
                            print(f"🔍 [REPLACE] Ищем: '{original_part[:50]}...'")
                            print(f"🔍 [REPLACE] Заменяем на: '{replacement_text}'")
                            print(f"🔍 [REPLACE] Тип файла: {'предпросмотр' if is_preview else 'умный шаблон'}")
                            
                            # Update paragraph text
                            paragraph.text = new_text
                            original_text = new_text  # Update for next iteration
                            applied_replacements.add(replacement_id)
                            
                            print(f"✅ [REPLACE] Применена замена: '{original_part[:30]}...' -> '{replacement_text}'")
                            
        except Exception as e:
            print(f"❌ [REPLACE] Ошибка при замене в параграфе: {e}")
            logger.error(f"Error applying replacement to paragraph: {e}")
    
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
                        # Удаляем желтую заливку перед применением форматирования
                        self._remove_highlighting(replacement_run)
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