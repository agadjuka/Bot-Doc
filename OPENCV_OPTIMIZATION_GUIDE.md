# OpenCV Оптимизация для Облачной Версии

## Проблема

OpenCV загружался при старте приложения в `main.py` через импорт `utils/receipt_analyzer.py`, что приводило к:

1. **Медленным ответам от Gemini** - OpenCV занимал память и ресурсы CPU
2. **Высокому потреблению памяти** - OpenCV оставался в памяти даже когда не использовался
3. **Блокировке других операций** - тяжелые операции OpenCV могли замедлять работу AI сервиса

## Решение

Реализована **ленивая загрузка OpenCV** с автоматической выгрузкой:

### 1. Ленивый загрузчик OpenCV (`utils/opencv_lazy_loader.py`)

```python
from utils.opencv_lazy_loader import get_opencv, unload_opencv, OpenCVContext

# Загружает OpenCV только при первом вызове
cv2 = get_opencv()

# Выгружает OpenCV из памяти
unload_opencv()

# Контекстный менеджер для автоматической загрузки/выгрузки
with OpenCVContext() as cv2:
    # OpenCV доступен здесь
    pass
# OpenCV автоматически выгружается
```

### 2. Оптимизированный анализатор (`utils/receipt_analyzer_optimized.py`)

- OpenCV загружается только при анализе изображения
- Автоматически выгружается после завершения анализа
- Проверяет доступность OpenCV перед загрузкой

### 3. Обновленный анализатор (`utils/receipt_analyzer.py`)

- Ленивая загрузка OpenCV через `_get_cv2()`
- Функция `unload_opencv()` для освобождения памяти
- Все функции используют ленивую загрузку

### 4. Обновленный обработчик фото (`handlers/photo_handler.py`)

```python
# Использует оптимизированную версию
from utils.receipt_analyzer_optimized import analyze_receipt_and_choose_model

# Анализ с автоматической загрузкой/выгрузкой OpenCV
chosen_model = await analyze_receipt_and_choose_model(image_bytes)

# Дополнительная выгрузка для гарантии
from utils.receipt_analyzer import unload_opencv
unload_opencv()
```

## Преимущества

### 🚀 Производительность
- **OpenCV загружается только при необходимости** - не при старте приложения
- **Автоматическая выгрузка** - освобождает память после использования
- **Быстрые ответы от Gemini** - нет блокировки ресурсов

### 💾 Память
- **Экономия памяти** - OpenCV не занимает память постоянно
- **Принудительная сборка мусора** - после выгрузки OpenCV
- **Мониторинг использования памяти** - встроенные логи

### 🔧 Надежность
- **Проверка доступности** - перед загрузкой OpenCV
- **Обработка ошибок** - graceful fallback если OpenCV недоступен
- **Обратная совместимость** - старый код продолжает работать

## Использование

### Для новых функций

```python
from utils.opencv_lazy_loader import with_opencv_async, OpenCVContext

# Декоратор для асинхронных функций
@with_opencv_async
async def my_opencv_function(cv2, image_bytes):
    # OpenCV автоматически загружается и выгружается
    return processed_image

# Контекстный менеджер
async def process_image(image_bytes):
    with OpenCVContext() as cv2:
        # OpenCV доступен здесь
        image = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
        # ... обработка ...
    # OpenCV автоматически выгружается
```

### Для существующих функций

```python
from utils.receipt_analyzer import _get_cv2, unload_opencv

def my_function():
    cv2 = _get_cv2()  # Ленивая загрузка
    try:
        # Используем OpenCV
        result = cv2.some_operation()
        return result
    finally:
        unload_opencv()  # Выгрузка
```

## Мониторинг

### Логи загрузки/выгрузки

```
🔍 Загружаем OpenCV для анализа изображения...
✅ OpenCV загружен успешно
🧹 Выгружаем OpenCV из памяти...
✅ OpenCV выгружен из памяти
```

### Проверка доступности

```python
from utils.opencv_lazy_loader import check_opencv_availability

if check_opencv_availability():
    print("OpenCV доступен")
else:
    print("OpenCV недоступен")
```

## Тестирование

Запустите тест оптимизации:

```bash
python test_opencv_optimization.py
```

Тест проверяет:
- Ленивую загрузку OpenCV
- Использование памяти до/после загрузки
- Выгрузку и освобождение памяти
- Повторную загрузку
- Функцию анализа изображений

## Результаты

### До оптимизации
- OpenCV загружался при старте приложения
- Занимал ~50-100 MB памяти постоянно
- Мог блокировать работу Gemini
- Медленные ответы от AI сервиса

### После оптимизации
- OpenCV загружается только при анализе фото
- Память освобождается после использования
- Gemini работает без блокировок
- Быстрые ответы от AI сервиса

## Совместимость

- ✅ **Обратная совместимость** - старый код работает без изменений
- ✅ **Облачная версия** - оптимизирована для Cloud Run
- ✅ **Локальная версия** - работает в обеих средах
- ✅ **Тестирование** - встроенные тесты производительности

## Рекомендации

1. **Используйте оптимизированную версию** для новых функций
2. **Мониторьте использование памяти** в логах
3. **Тестируйте производительность** регулярно
4. **Обновляйте существующий код** постепенно

## Файлы

- `utils/opencv_lazy_loader.py` - Ленивый загрузчик OpenCV
- `utils/receipt_analyzer_optimized.py` - Оптимизированный анализатор
- `utils/receipt_analyzer.py` - Обновленный анализатор с ленивой загрузкой
- `handlers/photo_handler.py` - Обновленный обработчик фото
- `test_opencv_optimization.py` - Тест оптимизации
- `main.py` - Обновленный main с проверкой OpenCV


