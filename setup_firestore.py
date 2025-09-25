#!/usr/bin/env python3
"""
Скрипт для настройки Firestore базы данных
"""
import os
from google.cloud import firestore
from google.cloud.exceptions import NotFound

def setup_firestore():
    """Настройка Firestore базы данных"""
    try:
        # Инициализация клиента Firestore с базой данных docbot
        db = firestore.Client(database='docbot')
        print("✅ Firestore клиент инициализирован успешно (база: docbot)")
        
        # Проверяем, существует ли коллекция user_languages
        try:
            # Пытаемся создать тестовый документ
            test_doc_ref = db.collection('user_languages').document('test')
            test_doc_ref.set({'test': 'value'})
            
            # Удаляем тестовый документ
            test_doc_ref.delete()
            
            print("✅ База данных Firestore доступна и работает")
            print("✅ Коллекция 'user_languages' готова к использованию")
            
        except Exception as e:
            print(f"❌ Ошибка при работе с Firestore: {e}")
            print("💡 Возможно, нужно создать базу данных в Google Cloud Console")
            print("🔗 Перейдите по ссылке: https://console.cloud.google.com/firestore?project=bot-doc-473208")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка инициализации Firestore: {e}")
        print("💡 Убедитесь, что:")
        print("   1. Переменная GOOGLE_APPLICATION_CREDENTIALS установлена")
        print("   2. Файл с учетными данными существует и доступен")
        print("   3. Учетная запись имеет права на Firestore")
        return False
    
    return True

if __name__ == "__main__":
    print("🔧 Настройка Firestore базы данных...")
    print("=" * 50)
    
    success = setup_firestore()
    
    if success:
        print("=" * 50)
        print("🎉 Firestore настроен успешно!")
        print("Теперь можно запускать бота.")
    else:
        print("=" * 50)
        print("❌ Настройка Firestore не удалась.")
        print("Следуйте инструкциям выше для исправления проблем.")
