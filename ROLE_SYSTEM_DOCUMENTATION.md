# Role System Documentation

## Обзор

Система ролей и разрешений для AI Bot, которая обеспечивает контроль доступа к функциям бота через роли пользователей и whitelist.

## Структура данных в Firestore

### Коллекция `users`
Каждый документ пользователя содержит:
- `role` (string): Роль пользователя ("admin" или "user")
- `display_mode` (string): Режим отображения таблиц ("desktop" или "mobile")
- `display_mode_updated_at` (timestamp): Время последнего обновления режима отображения
- Другие поля пользователя (ingredient_list, language, etc.)

### Коллекция `whitelist`
Документы с ID равным username пользователя (в нижнем регистре, без @):
- Документ может быть пустым
- ID документа = username пользователя

## Роли пользователей

### Admin (Администратор)
- Полный доступ ко всем функциям бота
- Управление whitelist
- Просмотр системной информации
- Автоматически назначается при первом запуске бота

### User (Пользователь)
- Стандартный доступ к функциям бота
- Ограниченные права доступа

## Система доступа

Пользователь имеет доступ к боту, если:
1. Он является администратором (role = "admin"), ИЛИ
2. Его username находится в whitelist

## Компоненты системы

### 1. UserService (`services/user_service.py`)
Основной сервис для управления пользователями и ролями:

#### Методы:
- `get_user_role(user_id)` - проверить, имеет ли пользователь роль "user"
- `set_user_role(user_id, role)` - установить роль пользователя
- `ensure_admin_role(admin_user_id)` - убедиться, что пользователь имеет роль admin
- `is_user_admin(user_id)` - проверить, является ли пользователь администратором
- `is_user_whitelisted(username)` - проверить, находится ли пользователь в whitelist
- `add_to_whitelist(username)` - добавить пользователя в whitelist
- `remove_from_whitelist(username)` - удалить пользователя из whitelist
- `get_whitelist()` - получить список всех пользователей в whitelist
- `get_user_info(user_id)` - получить полную информацию о пользователе
- `set_user_display_mode(user_id, mode)` - установить режим отображения таблиц
- `get_user_display_mode(user_id)` - получить режим отображения таблиц

### 2. RoleInitializer (`utils/role_initializer.py`)
Утилита для инициализации ролей при запуске бота:

#### Функции:
- `initialize_roles_and_permissions(db)` - инициализировать роли и разрешения
- `check_user_permissions(user_id, username, db)` - проверить права доступа пользователя

### 3. Конфигурация (`config/settings.py`)
- `ADMIN_TELEGRAM_ID` - ID администратора (261617302)

## Команды бота

### Для всех пользователей:
- `/start` - запуск бота (с проверкой доступа)
- `/dashboard` - панель управления

### Только для администраторов:
- `/admin` - панель администратора
- `/add_whitelist <username>` - добавить пользователя в whitelist
- `/remove_whitelist <username>` - удалить пользователя из whitelist
- `/list_whitelist` - показать список пользователей в whitelist

## Инициализация при запуске

При запуске бота автоматически:
1. Проверяется, есть ли у администратора роль "admin"
2. Если нет - назначается роль "admin"
3. Создается коллекция whitelist (при первом добавлении пользователя)

## Примеры использования

### Проверка доступа пользователя
```python
from utils.role_initializer import check_user_permissions

permissions = await check_user_permissions(user_id, username, db)
if permissions['has_access']:
    # Пользователь имеет доступ
    pass
```

### Добавление пользователя в whitelist
```python
from services.user_service import get_user_service

user_service = get_user_service(db)
success = await user_service.add_to_whitelist("username")
```

### Проверка роли администратора
```python
from services.user_service import get_user_service

user_service = get_user_service(db)
is_admin = await user_service.is_user_admin(user_id)
```

### Управление режимом отображения таблиц
```python
from services.user_service import get_user_service

user_service = get_user_service(db)

# Установить режим отображения
success = await user_service.set_user_display_mode(user_id, "desktop")
success = await user_service.set_user_display_mode(user_id, "mobile")

# Получить текущий режим отображения
display_mode = await user_service.get_user_display_mode(user_id)
# Возвращает "desktop" или "mobile", по умолчанию "mobile"
```

## Безопасность

1. Все команды администратора проверяют права доступа
2. Доступ к боту ограничен для неавторизованных пользователей
3. Роли хранятся в Firestore с защитой от несанкционированного доступа
4. Whitelist управляется только администраторами

## Тестирование

Для тестирования системы ролей используйте:
```bash
python test_role_system.py
```

Этот скрипт проверит:
- Инициализацию ролей
- Операции с whitelist
- Проверку разрешений
- Структуру данных в Firestore

## Миграция существующих пользователей

Существующие пользователи автоматически получат роль "user" при первом обращении к боту. Администратор получит роль "admin" при первом запуске бота.

## Логирование

Все операции с ролями и whitelist логируются в консоль с соответствующими эмодзи:
- ✅ Успешные операции
- ❌ Ошибки
- 🔧 Инициализация
- 👤 Операции с пользователями
- 📋 Операции с whitelist
