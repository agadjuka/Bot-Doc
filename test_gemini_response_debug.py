#!/usr/bin/env python3
"""
Тестовый скрипт для отладки парсинга ответа от Gemini
"""
import json
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv("env.local")

# Устанавливаем переменную окружения для Google Cloud
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "bot-doc-473208-706e6adceee1.json"

from services.template_processor_service import TemplateProcessorService

def test_gemini_response_parsing():
    """Тестируем парсинг ответа от Gemini"""
    
    # Читаем существующий ответ от Gemini
    with open("gemini_request_TemplateProcessorService_20250928_202156_318890_response.json", "r", encoding="utf-8") as f:
        response_data = json.load(f)
    
    gemini_response = response_data["response_text"]
    print(f"📄 Ответ от Gemini ({len(gemini_response)} символов):")
    print("=" * 50)
    print(gemini_response)
    print("=" * 50)
    
    # Инициализируем сервис
    service = TemplateProcessorService()
    
    # Парсим ответ
    print("\n🔍 Парсим ответ от Gemini...")
    edits_plan = service._parse_gemini_edits_plan(gemini_response)
    
    print(f"\n📊 Результат парсинга:")
    print(f"✅ Извлечено {len(edits_plan)} правок")
    
    for i, edit in enumerate(edits_plan):
        print(f"  {i+1}. run_id={edit['run_id']}, field_name='{edit['field_name']}'")
    
    return edits_plan

if __name__ == "__main__":
    test_gemini_response_parsing()
