"""
ВРЕМЕННАЯ ДЕБАГ-ФУНКЦИЯ ДЛЯ ЛОГИРОВАНИЯ ЗАПРОСОВ К GEMINI
ЭТОТ ФАЙЛ МОЖНО БЕЗОПАСНО УДАЛИТЬ ПОСЛЕ ОТЛАДКИ
"""
import os
import json
import datetime
from typing import Optional
import shutil


class GeminiDebugLogger:
    """
    Временный класс для логирования всех запросов к Gemini API.
    Автоматически очищает папку при инициализации.
    """
    
    def __init__(self, debug_folder: str = "debug_gemini_logs"):
        """
        Инициализация дебаг-логгера
        
        Args:
            debug_folder: Папка для хранения логов (будет создана в корне проекта)
        """
        # Получаем корневую папку проекта
        project_root = os.path.dirname(os.path.abspath(__file__))
        self.debug_folder = os.path.join(project_root, debug_folder)
        
        # Очищаем папку при инициализации
        self._cleanup_debug_folder()
        
        # Создаем папку заново
        os.makedirs(self.debug_folder, exist_ok=True)
        
        print(f"🔍 Gemini Debug Logger инициализирован: {self.debug_folder}")
    
    def _cleanup_debug_folder(self):
        """Очищает папку с дебаг-логами"""
        if os.path.exists(self.debug_folder):
            try:
                shutil.rmtree(self.debug_folder)
                print(f"🧹 Очищена папка дебаг-логов: {self.debug_folder}")
            except Exception as e:
                print(f"⚠️ Не удалось очистить папку дебаг-логов: {e}")
    
    def log_gemini_request(self, 
                          prompt: str, 
                          service_name: str = "unknown",
                          user_id: Optional[str] = None,
                          additional_info: Optional[dict] = None) -> str:
        """
        Логирует запрос к Gemini API
        
        Args:
            prompt: Текст запроса к Gemini
            service_name: Название сервиса, который делает запрос
            user_id: ID пользователя (если доступен)
            additional_info: Дополнительная информация для логирования
            
        Returns:
            Путь к созданному файлу лога
        """
        try:
            # Убеждаемся, что папка существует
            os.makedirs(self.debug_folder, exist_ok=True)
            
            # Создаем уникальное имя файла с временной меткой
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"gemini_request_{service_name}_{timestamp}.json"
            filepath = os.path.join(self.debug_folder, filename)
            
            # Подготавливаем данные для логирования
            log_data = {
                "timestamp": datetime.datetime.now().isoformat(),
                "service_name": service_name,
                "user_id": user_id,
                "prompt_length": len(prompt),
                "prompt_text": prompt,
                "additional_info": additional_info or {}
            }
            
            # Записываем в файл
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
            
            print(f"📝 Gemini запрос записан: {filename} ({len(prompt)} символов)")
            return filepath
            
        except Exception as e:
            print(f"❌ Ошибка записи дебаг-лога: {e}")
            return ""
    
    def log_gemini_response(self, 
                           response: str, 
                           request_filepath: str,
                           success: bool = True,
                           error_message: Optional[str] = None) -> str:
        """
        Логирует ответ от Gemini API
        
        Args:
            response: Ответ от Gemini
            request_filepath: Путь к файлу с запросом
            success: Успешность запроса
            error_message: Сообщение об ошибке (если есть)
            
        Returns:
            Путь к созданному файлу с ответом
        """
        try:
            # Убеждаемся, что папка существует
            os.makedirs(self.debug_folder, exist_ok=True)
            
            # Создаем имя файла для ответа на основе файла запроса
            base_name = os.path.splitext(os.path.basename(request_filepath))[0]
            response_filename = f"{base_name}_response.json"
            response_filepath = os.path.join(self.debug_folder, response_filename)
            
            # Подготавливаем данные для логирования ответа
            response_data = {
                "timestamp": datetime.datetime.now().isoformat(),
                "success": success,
                "response_length": len(response) if response else 0,
                "response_text": response,
                "error_message": error_message,
                "original_request_file": os.path.basename(request_filepath)
            }
            
            # Записываем в файл
            with open(response_filepath, 'w', encoding='utf-8') as f:
                json.dump(response_data, f, ensure_ascii=False, indent=2)
            
            print(f"📝 Gemini ответ записан: {response_filename} ({len(response) if response else 0} символов)")
            return response_filepath
            
        except Exception as e:
            print(f"❌ Ошибка записи дебаг-лога ответа: {e}")
            return ""
    
    def get_debug_folder_path(self) -> str:
        """Возвращает путь к папке с дебаг-логами"""
        return self.debug_folder
    
    def cleanup(self):
        """Ручная очистка папки с дебаг-логами"""
        self._cleanup_debug_folder()


# Глобальный экземпляр логгера для использования во всех сервисах
debug_logger = GeminiDebugLogger()


def log_gemini_request(prompt: str, service_name: str = "unknown", **kwargs) -> str:
    """
    Удобная функция для логирования запроса к Gemini
    
    Args:
        prompt: Текст запроса к Gemini
        service_name: Название сервиса
        **kwargs: Дополнительные параметры
        
    Returns:
        Путь к созданному файлу лога
    """
    return debug_logger.log_gemini_request(prompt, service_name, **kwargs)


def log_gemini_response(response: str, request_filepath: str, **kwargs) -> str:
    """
    Удобная функция для логирования ответа от Gemini
    
    Args:
        response: Ответ от Gemini
        request_filepath: Путь к файлу с запросом
        **kwargs: Дополнительные параметры
        
    Returns:
        Путь к созданному файлу с ответом
    """
    return debug_logger.log_gemini_response(response, request_filepath, **kwargs)


def cleanup_debug_logs():
    """Удобная функция для очистки дебаг-логов"""
    debug_logger.cleanup()
    print("🧹 Дебаг-логи очищены")


# Информация для разработчика
print("""
🔍 GEMINI DEBUG LOGGER ЗАГРУЖЕН
===============================
Эта функция создает временную папку 'debug_gemini_logs' в корне проекта
и записывает туда все запросы и ответы к Gemini API.

Для удаления дебага:
1. Удалите файл debug_gemini_logger.py
2. Удалите папку debug_gemini_logs/
3. Уберите импорты из других файлов

Папка автоматически очищается при каждом запуске бота.
===============================
""")
