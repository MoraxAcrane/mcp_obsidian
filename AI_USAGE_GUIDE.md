# 🤖 AI Usage Guide - Enhanced Obsidian MCP Server

## Для разработчиков ИИ и нейросетей

Этот MCP сервер специально оптимизирован для понимания ИИ с детальными описаниями, примерами и системными промптами.

---

## 🎯 Системные промпты для ИИ

### Основной промпт для работы с Obsidian MCP:
```
Ты - ИИ-ассистент, работающий с системой управления знаниями Obsidian через MCP сервер.

У тебя есть доступ к расширенным инструментам:

АНАЛИЗ И ОБЗОР:
• vault_overview - получи полную аналитику vault (здоровье, связность, рекомендации)
• read_note_enhanced - читай заметки с богатыми метаданными (статистика, связи, структура)
• note_exists - проверяй существование заметок перед операциями

УМНОЕ СОЗДАНИЕ:
• create_note_smart - создавай заметки с автотегами, предложениями папок и связей
• append_to_note - добавляй контент с умным форматированием и временными метками
• create_folder - создавай структурированные папки с индексами

БАЗОВЫЕ ОПЕРАЦИИ (совместимость):
• list_notes, create_note, read_note, update_note, delete_note, create_link

ПРАВИЛА:
1. Всегда начинай с vault_overview для понимания контекста vault
2. Используй note_exists перед созданием заметок
3. Предпочитай enhanced версии инструментов (они дают больше информации)
4. Анализируй полученные данные и давай рекомендации пользователю
```

### Промпт для анализа vault:
```
При анализе vault всегда:
1. Запроси vault_overview с include_detailed_stats: true
2. Обрати внимание на connectivity_ratio (связность заметок)
3. Найди orphaned_notes (изолированные заметки) 
4. Проанализируй folder_organization
5. Дай конкретные рекомендации по улучшению
```

### Промпт для создания заметок:
```
При создании заметок:
1. Используй create_note_smart для автоматических улучшений
2. Включи auto_enhance: true для автотегов
3. Включи suggest_connections: true для предложений связей
4. Проанализируй suggested_connections и создай важные связи
5. Если предложена папка - объясни почему
```

---

## 📋 Карты инструментов по use case

### 📊 АНАЛИЗ VAULT
```
Цель: Понять структуру и здоровье базы знаний

Последовательность:
1. vault_overview → получить общую картину
2. read_note_enhanced → детально изучить ключевые заметки  
3. Дать рекомендации по улучшению

Пример запроса:
{
  "tool": "vault_overview",
  "args": {"include_detailed_stats": true}
}

Ожидаемые данные:
- total_notes, connectivity_ratio, orphaned_notes
- recommendations массив с конкретными советами
- health_metrics для оценки качества
```

### ✨ УМНОЕ СОЗДАНИЕ КОНТЕНТА
```  
Цель: Создать качественно связанную заметку

Последовательность:
1. note_exists → проверить дубликаты
2. create_note_smart → создать с автоулучшениями
3. Проанализировать suggested_connections 
4. create_link → установить важные связи

Пример запроса:
{
  "tool": "create_note_smart", 
  "args": {
    "title": "React Hooks",
    "content": "# React Hooks\n\nПозволяют использовать состояние в функциональных компонентах.\n\n#programming #react #javascript",
    "auto_enhance": true,
    "suggest_connections": true
  }
}

Ожидаемые улучшения:
- auto_tags: извлеченные из контента теги
- suggested_folder: предложенная папка
- suggested_connections: релевантные заметки для связи
```

### 📝 ДОПОЛНЕНИЕ ЗАМЕТОК
```
Цель: Добавить информацию к существующим заметкам

Последовательность:
1. read_note_enhanced → понять структуру заметки
2. append_to_note → добавить контент с форматированием

Стили форматирования:
- "bullet" → маркированный список
- "heading" → как заголовок  
- "paragraph" → как параграф
- "append" → простое добавление

Пример запроса:
{
  "tool": "append_to_note",
  "args": {
    "title": "React Hooks", 
    "content": "useState позволяет добавить локальное состояние",
    "section": "Core Hooks",
    "format_style": "bullet",
    "add_timestamp": true
  }
}
```

### 🏗️ СТРУКТУРИРОВАНИЕ
```
Цель: Организовать заметки в логичную структуру

Последовательность:
1. vault_overview → оценить текущую организацию
2. create_folder → создать необходимые папки
3. Переместить заметки (через update операции)

Шаблоны индексов:
- "basic" → простой список
- "moc" → Map of Content со связями
- "structured" → с эмодзи и секциями

Пример запроса:
{
  "tool": "create_folder",
  "args": {
    "folder_path": "Programming/Frontend", 
    "create_index": true,
    "index_template": "structured"
  }
}
```

---

## 🔄 Типичные workflow для ИИ

### Workflow 1: "Создание новой области знаний"
```python
# 1. Проверить текущее состояние
vault_overview()

# 2. Создать структуру папок
create_folder("Machine Learning", template="moc")

# 3. Создать основную заметку
create_note_smart(
    title="Machine Learning - Overview",
    content="# Machine Learning\n\nОсновы машинного обучения...",
    auto_enhance=True
)

# 4. Создать связанные заметки
create_note_smart("Supervised Learning", content="...", suggest_connections=True)
create_note_smart("Neural Networks", content="...", suggest_connections=True)

# 5. Установить связи между концепциями
create_link("Machine Learning - Overview", "Supervised Learning", bidirectional=True)
```

### Workflow 2: "Анализ и улучшение существующего vault"
```python
# 1. Полный анализ
analysis = vault_overview(include_detailed_stats=True)

# 2. Работа с изолированными заметками
for orphan in analysis["orphaned_notes"]:
    note_data = read_note_enhanced(orphan, include_metadata=True)
    # Анализировать контент и предлагать связи
    
# 3. Улучшение связности
# Найти заметки с похожими темами и связать их
```

### Workflow 3: "Исследование темы"  
```python
# 1. Проверить существование
exists = note_exists("Topic Name", return_suggestions=True)

# 2. Если есть похожие - изучить их
if exists["suggestions"]:
    for suggestion in exists["suggestions"]:
        note_data = read_note_enhanced(suggestion, include_metadata=True)
        
# 3. Создать новую заметку на основе анализа
create_note_smart("Topic Name", content="...", suggest_connections=True)
```

---

## ⚡ Оптимальные паттерны для ИИ

### 🎯 Всегда начинать с контекста:
```python
# ХОРОШО: Понимаем контекст перед действием
vault_data = vault_overview()
if vault_data["overview"]["total_notes"] == 0:
    # Vault пустой - создаем базовую структуру
    create_folder("Getting Started", create_index=True)
else:
    # Анализируем существующую структуру
    connectivity = vault_data["health_metrics"]["connectivity_ratio"]
    if connectivity < 20:
        # Низкая связность - фокус на создании связей
```

### 🔗 Максимизировать связность:
```python
# При создании заметки всегда анализировать предложения
result = create_note_smart(title, content, suggest_connections=True)
for connection in result["suggested_connections"]:
    # Оценить релевантность и создать связь
    if relevance_score(connection) > 0.7:
        create_link(title, connection["note"], context=connection["reason"])
```

### 📊 Использовать метаданные для решений:
```python
note_data = read_note_enhanced(title, include_metadata=True) 
stats = note_data["enhanced_metadata"]["content_stats"]

if stats["word_count"] < 50:
    # Короткая заметка - предложить расширение
    append_to_note(title, "## Детали\n\n[Добавить подробности]")
    
if stats["link_count"] == 0:
    # Изолированная заметка - найти связи
    # ... логика поиска связей
```

---

## 🚨 Важные принципы для ИИ

### ✅ DO - Правильно:
- Всегда используй enhanced версии инструментов когда доступны
- Проверяй существование заметок перед созданием
- Анализируй предложенные связи и создавай релевантные
- Используй богатые метаданные для принятия решений
- Давай конкретные рекомендации пользователю

### ❌ DON'T - Неправильно:
- Не создавай заметки без проверки дубликатов
- Не игнорируй предложения автоулучшений
- Не создавай изолированные заметки без попыток связать
- Не используй базовые инструменты если есть enhanced версии
- Не забывай про анализ здоровья vault

---

## 📈 Метрики качества для ИИ

### Оценивай результат по метрикам:
```python
vault_health = vault_overview()["health_metrics"]

# Хорошие показатели:
# connectivity_ratio > 60% - хорошая связность
# orphaned_notes_count < 10% от total_notes - мало изолированных
# folder_organization == "good" - есть структура

# Рекомендации для улучшения:
if connectivity_ratio < 30:
    print("🔗 Критично: Низкая связность - создавай больше связей")
if orphaned_notes_count > total_notes * 0.2:
    print("🏝️ Много изолированных заметок - анализируй и связывай")
```

Этот guide поможет ИИ эффективно использовать все возможности enhanced MCP сервера! 🚀
