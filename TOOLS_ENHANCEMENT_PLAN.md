# 🔧 Enhanced Tools Upgrade Plan

**Философия**: Меньше инструментов, больше возможностей в каждом

---

## 🎯 **ПРИНЦИП: POWER THROUGH PARAMETERS**

### ✅ **Преимущества подхода:**
- **Меньше cognitive load** для ИИ (не надо выбирать из 32 инструментов)
- **Интуитивнее** для пользователей (одна функция - много возможностей)
- **Легче поддерживать** код (centralized логика)
- **Лучше документировать** (все опции в одном месте)

### ❌ **Проблемы множества инструментов:**
- Playwright MCP: 32 инструмента - overwhelming choice
- Трудно найти нужный инструмент
- Дублирование функциональности
- Сложность в поддержке

---

## 🚀 **ПЛАН РАСШИРЕНИЯ СУЩЕСТВУЮЩИХ ИНСТРУМЕНТОВ**

### 1. **🔍 `explore_notes` → SUPER SEARCH ENGINE**

#### **Текущие возможности:**
```python
explore_notes(keywords, search_in="all", language_flexible=True, limit=15)
```

#### **🎯 Расширенные возможности:**
```python
explore_notes(
    # Основной поиск
    keywords: str = "",
    search_in: str = "all",  # "all", "titles", "content", "tags"
    
    # 🏷️ ФИЛЬТРЫ ПО ТЕГАМ
    include_tags: Optional[List[str]] = None,     # Только с этими тегами
    exclude_tags: Optional[List[str]] = None,     # Исключить эти теги  
    require_all_tags: bool = False,              # Все теги или любой
    
    # 📅 ВРЕМЕННЫЕ ФИЛЬТРЫ
    created_after: Optional[str] = None,         # "2024-01-01" 
    created_before: Optional[str] = None,        # "2024-12-31"
    modified_after: Optional[str] = None,        # Недавно измененные
    modified_before: Optional[str] = None,       # Давно не обновляемые
    
    # 📁 СТРУКТУРНЫЕ ФИЛЬТРЫ  
    folders: Optional[List[str]] = None,         # Поиск в папках
    exclude_folders: Optional[List[str]] = None, # Исключить папки
    min_links: Optional[int] = None,             # Минимум исходящих ссылок
    max_links: Optional[int] = None,             # Максимум ссылок
    
    # 📊 РАЗМЕР И КАЧЕСТВО
    min_words: Optional[int] = None,             # Минимум слов в заметке
    max_words: Optional[int] = None,             # Максимум слов
    has_tasks: Optional[bool] = None,            # Содержит чекбоксы [ ]
    
    # 🎯 ПОВЕДЕНИЕ ПОИСКА
    language_flexible: bool = True,              # Rus/Eng транслитерация
    case_sensitive: bool = False,                # Регистрозависимость
    fuzzy_matching: bool = True,                 # Исправление опечаток
    semantic_search: bool = False,               # AI-поиск по смыслу (Phase 2)
    
    # 📋 РЕЗУЛЬТАТЫ
    limit: int = 15,                             # Количество результатов
    sort_by: str = "relevance",                  # "relevance", "modified", "created", "title"
    group_by: Optional[str] = None,              # "folder", "tags", "date"
    include_content_preview: bool = True,        # Превью содержимого
    include_metadata: bool = True,               # Теги, даты, размеры
    include_similar: bool = False,               # Похожие заметки (Phase 2)
    
    # 🎨 ВИЗУАЛИЗАЦИЯ
    highlight_matches: bool = True,              # Подсветка найденного
    min_relevance: float = 0.1                   # Минимальная релевантность
) -> Dict[str, Any]
```

#### **🎪 Примеры использования:**
```python
# Базовый поиск как раньше
explore_notes("machine learning")

# Поиск с фильтрами по тегам
explore_notes("productivity", include_tags=["work", "active"], exclude_tags=["archive"])

# Поиск недавно измененных заметок о программировании
explore_notes("programming", modified_after="2024-09-01", folders=["Projects"])

# Поиск коротких заметок без ссылок (потенциально недоработанные)  
explore_notes("", max_words=100, max_links=0, sort_by="modified")

# Поиск заметок с задачами в рабочих папках
explore_notes("", has_tasks=True, folders=["Work", "Projects"], sort_by="created")
```

---

### 2. **📋 `list_notes` → SMART NOTE BROWSER**

#### **Текущие возможности:**
```python
list_notes(folder=None, limit=20)
```

#### **🎯 Расширенные возможности:**
```python
list_notes(
    # 📁 ОБЛАСТЬ ПОИСКА
    folder: Optional[str] = None,                # Конкретная папка
    recursive: bool = True,                      # Включая подпапки
    
    # 🏷️ ФИЛЬТРАЦИЯ
    include_tags: Optional[List[str]] = None,    # Только с тегами
    exclude_tags: Optional[List[str]] = None,    # Исключить теги
    status_filter: Optional[str] = None,         # "active", "completed", "draft"
    
    # ⏰ ВРЕМЕННАЯ ФИЛЬТРАЦИЯ
    days_back: Optional[int] = None,             # Последние N дней
    created_after: Optional[str] = None,         # После даты
    modified_after: Optional[str] = None,        # Измененные после
    
    # 📊 КРИТЕРИИ ОТБОРА
    min_words: Optional[int] = None,             # Минимум слов
    has_links: Optional[bool] = None,            # Содержит ссылки
    has_tags: Optional[bool] = None,             # Содержит теги
    orphaned: Optional[bool] = None,             # Без входящих ссылок
    
    # 📋 СОРТИРОВКА И ГРУППИРОВКА
    sort_by: str = "modified",                   # "modified", "created", "title", "size"
    sort_order: str = "desc",                    # "desc", "asc"
    group_by: Optional[str] = None,              # "folder", "tags", "date", "status"
    
    # 📄 РЕЗУЛЬТАТЫ
    limit: Optional[int] = 20,                   # Количество (max 50)
    include_preview: bool = False,               # Краткое содержимое
    include_stats: bool = True,                  # Статистика (слова, ссылки)
    include_backlinks: bool = False,             # Входящие ссылки
    
    # 📈 АНАЛИТИКА
    show_trends: bool = False,                   # Тренды изменений
    highlight_recent: bool = True                # Выделить недавние
) -> Dict[str, Any]
```

#### **🎪 Примеры использования:**
```python
# Классический список как раньше
list_notes()

# Активные проекты с задачами
list_notes(include_tags=["project", "active"], has_tasks=True, sort_by="modified")

# Orphaned notes (потенциально нужно связать)
list_notes(orphaned=True, limit=10)

# Заметки без тегов (нужно организовать)
list_notes(has_tags=False, min_words=50, sort_by="modified")

# Большие заметки из рабочих папок  
list_notes(folder="Work", min_words=500, include_preview=True)

# Недавняя активность по папкам
list_notes(days_back=7, group_by="folder", show_trends=True)
```

---

### 3. **✏️ `create_note` → SMART NOTE GENERATOR**

#### **Текущие возможности:**
```python
create_note(title, content, folder=None)
```

#### **🎯 Расширенные возможности:**
```python
create_note(
    title: str,
    content: str = "",
    
    # 📁 РАЗМЕЩЕНИЕ
    folder: Optional[str] = None,                # Целевая папка
    auto_folder: bool = False,                   # Авто-выбор папки по содержимому
    
    # 🏷️ ТЕГИРОВАНИЕ
    tags: Optional[List[str]] = None,            # Явные теги
    auto_tags: bool = False,                     # Авто-тегирование по содержимому
    inherit_tags: bool = False,                  # Наследовать теги папки
    
    # 🔗 СВЯЗЫВАНИЕ  
    link_to: Optional[List[str]] = None,         # Создать ссылки на заметки
    find_related: bool = False,                  # Найти похожие и связать
    create_backlinks: bool = False,              # Создать обратные ссылки
    
    # 📋 ШАБЛОНИЗАЦИЯ
    template: Optional[str] = None,              # "daily", "project", "meeting"
    variables: Optional[Dict] = None,            # Переменные для шаблона
    apply_structure: bool = True,                # Авто-структурирование
    
    # 📊 МЕТАДАННЫЕ
    priority: Optional[str] = None,              # "high", "medium", "low"  
    status: Optional[str] = None,                # "draft", "active", "completed"
    project: Optional[str] = None,               # Связь с проектом
    
    # 🎯 AI-ENHANCEMENT (Phase 2)
    enhance_content: bool = False,               # AI улучшение содержимого
    suggest_structure: bool = False,             # Предложить структуру
    find_connections: bool = False               # Найти связи с существующими
) -> Dict[str, Any]
```

#### **🎪 Примеры использования:**
```python
# Простое создание как раньше
create_note("My Idea", "Some content")

# Создание project note с автоматикой
create_note(
    "Project Alpha", 
    "New project description",
    template="project",
    auto_tags=True,
    find_related=True,
    status="active",
    priority="high"
)

# Daily note с шаблоном
create_note(
    "2024-09-24", 
    template="daily",
    variables={"focus": "MCP development", "energy": 8},
    auto_folder=True
)

# Meeting note с авто-связыванием
create_note(
    "Team Standup - Sept 24",
    "Discussion about...",
    template="meeting", 
    tags=["meeting", "team"],
    link_to=["Project Alpha", "Sprint Planning"],
    create_backlinks=True
)
```

---

### 4. **📖 `read_note` → DEEP NOTE ANALYZER**

#### **Текущие возможности:**
```python
read_note(title, include_backlinks=True, include_outlinks=True)
```

#### **🎯 Расширенные возможности:**
```python
read_note(
    title: str,
    
    # 📄 СОДЕРЖИМОЕ
    include_content: bool = True,                # Основное содержимое
    include_metadata: bool = True,               # Frontmatter и теги
    include_stats: bool = False,                 # Статистика (слова, ссылки)
    
    # 🔗 СВЯЗИ
    include_backlinks: bool = True,              # Входящие ссылки
    include_outlinks: bool = True,               # Исходящие ссылки
    analyze_connections: bool = False,           # Анализ связей (strength, type)
    connection_depth: int = 1,                   # Глубина анализа связей
    
    # 📊 АНАЛИТИКА
    include_similar: bool = False,               # Похожие заметки (Phase 2)
    similarity_threshold: float = 0.7,           # Порог похожести
    include_clusters: bool = False,              # Тематические кластеры
    
    # 📈 ИСТОРИЯ И ТРЕНДЫ
    include_history: bool = False,               # История изменений
    show_activity: bool = False,                 # Активность (views, edits)
    compare_versions: bool = False,              # Сравнение версий
    
    # 🎯 QUALITY ANALYSIS
    content_quality: bool = False,               # Оценка качества содержимого
    completeness_score: bool = False,            # Полнота информации  
    suggest_improvements: bool = False,          # Рекомендации улучшений
    
    # 📋 TASKS И ACTIONS
    extract_tasks: bool = False,                 # Найти все задачи [ ]
    extract_questions: bool = False,             # Найти вопросы ?
    extract_dates: bool = False,                 # Извлечь даты и дедлайны
    
    # 🔍 CONTEXT ANALYSIS
    topic_modeling: bool = False,                # Определить основные темы
    key_concepts: bool = False,                  # Ключевые концепции
    reading_time: bool = False                   # Время чтения
) -> Dict[str, Any]
```

#### **🎪 Примеры использования:**
```python
# Простое чтение как раньше
read_note("Project Alpha")

# Глубокий анализ заметки
read_note(
    "Project Alpha",
    include_stats=True,
    analyze_connections=True, 
    include_similar=True,
    content_quality=True,
    suggest_improvements=True
)

# Анализ задач и дедлайнов
read_note(
    "Weekly Planning",
    extract_tasks=True,
    extract_dates=True,
    show_activity=True
)

# Исследование связей
read_note(
    "Machine Learning Hub", 
    connection_depth=2,
    include_clusters=True,
    topic_modeling=True
)
```

---

## 📊 **РЕЗУЛЬТАТ АПГРЕЙДА**

### ✅ **Вместо 32 инструментов → 4 МОЩНЫХ:**
1. **`explore_notes`** - универсальный поиск с 20+ параметрами
2. **`list_notes`** - умное браузер заметок с фильтрами  
3. **`create_note`** - интеллектуальное создание с автоматикой
4. **`read_note`** - глубокий анализ заметок

### 🎯 **Преимущества:**
- **Меньше cognitive load** - ИИ не путается в выборе
- **Более мощные возможности** - каждый инструмент делает много
- **Backward compatibility** - старые вызовы работают как раньше
- **Легче документировать** - все опции в docstring

### 🚀 **Phase 2 интеграция:**
Семантический анализ добавляется как параметры:
- `semantic_search=True` в explore_notes
- `include_similar=True` в read_note  
- `auto_tags=True` в create_note
- `find_connections=True` везде

---

## 💡 **РЕАЛИЗАЦИЯ**

### 🎯 **Подход:**
1. **Расширить существующие функции** новыми параметрами
2. **Сохранить backward compatibility** - старые вызовы работают
3. **Добавлять постепенно** - по 2-3 параметра за раз
4. **Тестировать каждое расширение** - не ломать существующее

### 📋 **Порядок реализации:**
1. **explore_notes** - добавить фильтры по тегам и датам
2. **list_notes** - добавить сортировку и группировку  
3. **create_note** - добавить автотегирование и шаблоны
4. **read_note** - добавить аналитику и статистику

**Результат: 4 суперинструмента вместо множества специализированных! 🎯**
