#!/usr/bin/env python3
"""
Тестер для проверки системы обработки шаблонов
Использует существующий ответ от Gemini и тестирует внесение изменений в Word-документ
"""
import asyncio
import json
import os
from dotenv import load_dotenv
from docx import Document
from io import BytesIO

# Загружаем переменные окружения
load_dotenv("env.local")

# Устанавливаем переменную окружения для Google Cloud
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "bot-doc-473208-706e6adceee1.json"

from services.template_processor_service import TemplateProcessorService

class TemplateProcessorTester:
    """Тестер для проверки системы обработки шаблонов"""
    
    def __init__(self):
        self.service = TemplateProcessorService()
        self.test_document_path = "ДОГОВОР С АВТОКИТ!.docx"
        self.gemini_response_path = "gemini_request_TemplateProcessorService_20250928_202156_318890_response.json"
    
    def load_gemini_response(self):
        """Загружает ответ от Gemini из файла"""
        try:
            with open(self.gemini_response_path, "r", encoding="utf-8") as f:
                response_data = json.load(f)
            
            gemini_response = response_data["response_text"]
            print(f"📄 Загружен ответ от Gemini ({len(gemini_response)} символов)")
            return gemini_response
            
        except Exception as e:
            print(f"❌ Ошибка загрузки ответа от Gemini: {e}")
            return None
    
    def load_test_document(self):
        """Загружает тестовый Word-документ"""
        try:
            if not os.path.exists(self.test_document_path):
                print(f"❌ Тестовый документ не найден: {self.test_document_path}")
                return None
            
            with open(self.test_document_path, "rb") as f:
                file_bytes = f.read()
            
            print(f"📄 Загружен тестовый документ: {len(file_bytes)} байт")
            return file_bytes
            
        except Exception as e:
            print(f"❌ Ошибка загрузки документа: {e}")
            return None
    
    def parse_gemini_response(self, gemini_response):
        """Парсит ответ от Gemini и извлекает план правок"""
        print("\n🔍 Парсим ответ от Gemini...")
        edits_plan = self.service._parse_gemini_edits_plan(gemini_response)
        
        print(f"✅ Извлечено {len(edits_plan)} правок:")
        for i, edit in enumerate(edits_plan):
            print(f"  {i+1}. run_id={edit['run_id']}, field_name='{edit['field_name']}'")
        
        return edits_plan
    
    def analyze_document_structure(self, file_bytes):
        """Анализирует структуру документа и создает карту run'ов"""
        print("\n📊 Анализируем структуру документа...")
        
        # Загружаем документ
        doc = Document(BytesIO(file_bytes))
        
        # Создаем карту run'ов
        map_for_gemini, coords_dictionary = self.service._index_runs_and_build_map(doc)
        
        print(f"📊 Найдено {len(coords_dictionary)} run'ов в документе")
        print(f"🔍 Первые 10 run_id: {list(coords_dictionary.keys())[:10]}")
        print(f"🔍 Последние 10 run_id: {list(coords_dictionary.keys())[-10:]}")
        
        return doc, coords_dictionary
    
    def test_edits_application(self, doc, coords_dictionary, edits_plan):
        """Тестирует применение правок к документу"""
        print(f"\n🔧 Тестируем применение {len(edits_plan)} правок...")
        
        # Создаем копию документа для тестирования
        original_bytes = BytesIO()
        doc.save(original_bytes)
        original_bytes.seek(0)
        
        test_doc = Document(original_bytes)
        _, test_coords_dictionary = self.service._index_runs_and_build_map(test_doc)
        
        # Применяем правки
        successful_edits = 0
        failed_edits = 0
        
        for i, edit in enumerate(edits_plan):
            run_id = edit['run_id']
            field_name = edit['field_name']
            
            print(f"\n🔍 Правка {i+1}/{len(edits_plan)}: run_id={run_id}, field_name='{field_name}'")
            
            # Ищем run в тестовом документе
            test_run = test_coords_dictionary.get(run_id)
            
            if not test_run:
                print(f"❌ Run {run_id} не найден в тестовом документе")
                print(f"📊 Доступные run_id: {list(test_coords_dictionary.keys())[:10]}...")
                failed_edits += 1
                continue
            
            print(f"✅ Run {run_id} найден")
            print(f"📝 Текущий текст: '{test_run.text}'")
            
            # Применяем правку
            if field_name == "":
                print(f"🧹 Очищаю run {run_id}")
                test_run.text = ""
            else:
                print(f"✏️ Заменяю run {run_id} на '[{field_name}]'")
                test_run.text = f"[{field_name}]"
            
            print(f"📝 Новый текст: '{test_run.text}'")
            successful_edits += 1
        
        print(f"\n📊 Результат применения правок:")
        print(f"✅ Успешно применено: {successful_edits}")
        print(f"❌ Не удалось применить: {failed_edits}")
        
        return test_doc, successful_edits, failed_edits
    
    def save_test_results(self, test_doc, successful_edits, failed_edits):
        """Сохраняет результаты тестирования"""
        try:
            # Сохраняем тестовый документ
            test_output_path = "test_output_with_edits.docx"
            test_doc.save(test_output_path)
            print(f"💾 Тестовый документ сохранен: {test_output_path}")
            
            # Создаем отчет
            report_path = "test_report.txt"
            with open(report_path, "w", encoding="utf-8") as f:
                f.write("ОТЧЕТ О ТЕСТИРОВАНИИ СИСТЕМЫ ОБРАБОТКИ ШАБЛОНОВ\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Тестовый документ: {self.test_document_path}\n")
                f.write(f"Ответ от Gemini: {self.gemini_response_path}\n\n")
                f.write(f"Успешно применено правок: {successful_edits}\n")
                f.write(f"Не удалось применить: {failed_edits}\n")
                f.write(f"Результат сохранен в: {test_output_path}\n")
            
            print(f"📋 Отчет сохранен: {report_path}")
            
        except Exception as e:
            print(f"❌ Ошибка сохранения результатов: {e}")
    
    async def run_full_test(self):
        """Запускает полный тест системы обработки шаблонов"""
        print("🚀 ЗАПУСК ПОЛНОГО ТЕСТА СИСТЕМЫ ОБРАБОТКИ ШАБЛОНОВ")
        print("=" * 60)
        
        # Шаг 1: Загружаем ответ от Gemini
        gemini_response = self.load_gemini_response()
        if not gemini_response:
            return
        
        # Шаг 2: Загружаем тестовый документ
        file_bytes = self.load_test_document()
        if not file_bytes:
            return
        
        # Шаг 3: Парсим ответ от Gemini
        edits_plan = self.parse_gemini_response(gemini_response)
        if not edits_plan:
            print("❌ Не удалось извлечь план правок")
            return
        
        # Шаг 4: Анализируем структуру документа
        doc, coords_dictionary = self.analyze_document_structure(file_bytes)
        
        # Шаг 5: Тестируем применение правок
        test_doc, successful_edits, failed_edits = self.test_edits_application(
            doc, coords_dictionary, edits_plan
        )
        
        # Шаг 6: Сохраняем результаты
        self.save_test_results(test_doc, successful_edits, failed_edits)
        
        # Шаг 7: Итоговый отчет
        print("\n" + "=" * 60)
        print("📋 ИТОГОВЫЙ ОТЧЕТ")
        print("=" * 60)
        print(f"✅ Успешно применено правок: {successful_edits}")
        print(f"❌ Не удалось применить: {failed_edits}")
        print(f"📊 Процент успеха: {(successful_edits / len(edits_plan)) * 100:.1f}%")
        
        if failed_edits > 0:
            print("\n🔍 РЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ:")
            print("1. Проверьте соответствие run_id в ответе Gemini и в документе")
            print("2. Убедитесь, что документ не был изменен после создания карты run'ов")
            print("3. Проверьте логику индексации run'ов в методе _index_runs_and_build_map")
        else:
            print("\n🎉 ВСЕ ПРАВКИ ПРИМЕНЕНЫ УСПЕШНО!")

async def main():
    """Главная функция"""
    tester = TemplateProcessorTester()
    await tester.run_full_test()

if __name__ == "__main__":
    asyncio.run(main())
