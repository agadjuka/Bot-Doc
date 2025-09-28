"""
Document Generator Service for creating .docx and .doc files from templates
"""
import io
import os
from typing import Dict, Any, Optional
from docxtpl import DocxTemplate


class DocumentGeneratorService:
    """Service for generating .docx and .doc documents from templates"""
    
    def __init__(self, templates_dir: str = "templates"):
        """
        Initialize the Document Generator Service
        
        Args:
            templates_dir: Directory containing template files
        """
        self.templates_dir = templates_dir
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir)
            print(f"📁 Создана папка для шаблонов: {templates_dir}")
    
    def fill_document(self, template_path: str, data: Dict[str, Any]) -> bytes:
        """
        Fill a document template with provided data
        
        Args:
            template_path: Path to the .docx or .doc template file
            data: Dictionary with data to fill the template
            
        Returns:
            Bytes of the filled document
            
        Raises:
            FileNotFoundError: If template file doesn't exist
            Exception: If document generation fails
        """
        try:
            # Check if template file exists
            if not os.path.exists(template_path):
                raise FileNotFoundError(f"Шаблон не найден: {template_path}")
            
            # Load the template
            template = DocxTemplate(template_path)
            
            # Clean the data - replace None values with empty strings
            cleaned_data = {}
            for key, value in data.items():
                if value is None:
                    cleaned_data[key] = ""
                else:
                    cleaned_data[key] = str(value)
            
            # Render the template with data
            template.render(cleaned_data)
            
            # Save to memory
            doc_buffer = io.BytesIO()
            template.save(doc_buffer)
            doc_buffer.seek(0)
            
            print(f"✅ Документ успешно сгенерирован из шаблона: {template_path}")
            return doc_buffer.getvalue()
            
        except FileNotFoundError as e:
            print(f"❌ Ошибка: {e}")
            raise
        except Exception as e:
            print(f"❌ Ошибка при генерации документа: {e}")
            raise
    
    def get_template_path(self, template_name: str) -> str:
        """
        Get full path to a template file
        
        Args:
            template_name: Name of the template file (with or without .docx/.doc extension)
            
        Returns:
            Full path to the template file
        """
        if not (template_name.endswith('.docx') or template_name.endswith('.doc')):
            template_name += '.docx'  # Default to .docx if no extension
        
        return os.path.join(self.templates_dir, template_name)
    
