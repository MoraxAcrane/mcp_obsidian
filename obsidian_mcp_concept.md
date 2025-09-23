# AI-Powered Obsidian MCP Server
## Концепция интеллектуального управления базой знаний

### 📋 Общее описание проекта

Создание MCP (Model Context Protocol) сервера для полной интеграции ИИ с Obsidian, позволяющего нейросети автономно управлять базой знаний: создавать заметки, устанавливать связи, структурировать информацию и создавать интеллектуальную карту знаний.

### 🎯 Ключевые цели

1. **Автоматизация создания заметок** - ИИ самостоятельно создает структурированные заметки
2. **Интеллектуальное связывание** - автоматическое обнаружение и создание связей между концепциями
3. **Семантическая организация** - группировка и кластеризация заметок по смыслу
4. **Динамическая структура** - адаптивная организация знаний под потребности пользователя
5. **Контекстуальный поиск** - поиск не только по тексту, но и по семантике

## 🏗️ Архитектура системы

### Основные компоненты

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Claude AI     │◄──►│   MCP Server     │◄──►│   Obsidian      │
│                 │    │                  │    │   Vault         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Knowledge Graph │
                    │    Database      │
                    └──────────────────┘
```

### Технологический стек

- **Основа**: Python 3.11+ с asyncio
- **MCP Framework**: `mcp` библиотека от Anthropic
- **Обработка Markdown**: `python-markdown`, `frontmatter`
- **Семантический анализ**: `sentence-transformers`, `numpy`
- **База данных**: `sqlite3` для индексации и графа связей
- **Файловая система**: `watchdog` для мониторинга изменений
- **NLP обработка**: `spacy`, `nltk` для извлечения ключевых слов

## 🔧 Детальное API MCP сервера

### 1. Управление заметками

#### `create_note`
```python
{
    "name": "create_note",
    "description": "Создает новую заметку в Obsidian vault",
    "inputSchema": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Заголовок заметки"},
            "content": {"type": "string", "description": "Содержимое в Markdown"},
            "tags": {"type": "array", "items": {"type": "string"}},
            "folder": {"type": "string", "description": "Папка для размещения"},
            "template": {"type": "string", "description": "Шаблон заметки"}
        },
        "required": ["title", "content"]
    }
}
```

#### `read_note`
```python
{
    "name": "read_note",
    "description": "Читает содержимое заметки и её метаданные",
    "inputSchema": {
        "type": "object", 
        "properties": {
            "title": {"type": "string"},
            "include_backlinks": {"type": "boolean", "default": True},
            "include_outlinks": {"type": "boolean", "default": True}
        },
        "required": ["title"]
    }
}
```

#### `update_note`
```python
{
    "name": "update_note",
    "description": "Обновляет существующую заметку",
    "inputSchema": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "content": {"type": "string"},
            "append": {"type": "boolean", "description": "Добавить к существующему"},
            "section": {"type": "string", "description": "Конкретная секция для обновления"}
        },
        "required": ["title"]
    }
}
```

### 2. Управление связями

#### `create_link`
```python
{
    "name": "create_link",
    "description": "Создает связь между заметками",
    "inputSchema": {
        "type": "object",
        "properties": {
            "from_note": {"type": "string"},
            "to_note": {"type": "string"},
            "link_type": {
                "type": "string", 
                "enum": ["direct", "alias", "embed", "tag"],
                "default": "direct"
            },
            "context": {"type": "string", "description": "Контекст для связи"},
            "bidirectional": {"type": "boolean", "default": False}
        },
        "required": ["from_note", "to_note"]
    }
}
```

#### `analyze_connections`
```python
{
    "name": "analyze_connections",
    "description": "Анализирует существующие связи и предлагает новые",
    "inputSchema": {
        "type": "object",
        "properties": {
            "note_title": {"type": "string"},
            "depth": {"type": "integer", "default": 2},
            "suggest_new": {"type": "boolean", "default": True},
            "similarity_threshold": {"type": "number", "default": 0.7}
        }
    }
}
```

### 3. Поиск и навигация

#### `semantic_search`
```python
{
    "name": "semantic_search",
    "description": "Семантический поиск по заметкам",
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "limit": {"type": "integer", "default": 10},
            "include_content": {"type": "boolean", "default": False},
            "filter_tags": {"type": "array", "items": {"type": "string"}},
            "min_similarity": {"type": "number", "default": 0.5}
        },
        "required": ["query"]
    }
}
```

#### `get_knowledge_map`
```python
{
    "name": "get_knowledge_map",
    "description": "Получает структуру графа знаний",
    "inputSchema": {
        "type": "object",
        "properties": {
            "center_note": {"type": "string", "description": "Центральная заметка"},
            "radius": {"type": "integer", "default": 3},
            "include_orphans": {"type": "boolean", "default": False},
            "cluster_by": {
                "type": "string",
                "enum": ["topic", "date", "tag", "similarity"]
            }
        }
    }
}
```

### 4. Интеллектуальная структуризация

#### `auto_organize`
```python
{
    "name": "auto_organize",
    "description": "Автоматически организует заметки по темам",
    "inputSchema": {
        "type": "object",
        "properties": {
            "scope": {
                "type": "string",
                "enum": ["all", "unorganized", "folder", "tag"]
            },
            "target": {"type": "string", "description": "Целевая папка/тег"},
            "create_mocs": {"type": "boolean", "default": True},
            "min_cluster_size": {"type": "integer", "default": 3}
        }
    }
}
```

#### `extract_concepts`
```python
{
    "name": "extract_concepts",
    "description": "Извлекает ключевые концепции из текста",
    "inputSchema": {
        "type": "object",
        "properties": {
            "text": {"type": "string"},
            "max_concepts": {"type": "integer", "default": 10},
            "create_notes": {"type": "boolean", "default": False},
            "link_to_source": {"type": "boolean", "default": True}
        },
        "required": ["text"]
    }
}
```

## 📊 Структура данных

### База данных индексации

```sql
-- Таблица заметок
CREATE TABLE notes (
    id INTEGER PRIMARY KEY,
    title TEXT UNIQUE NOT NULL,
    file_path TEXT NOT NULL,
    content_hash TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    word_count INTEGER,
    embedding BLOB  -- векторное представление
);

-- Таблица связей
CREATE TABLE links (
    id INTEGER PRIMARY KEY,
    from_note_id INTEGER,
    to_note_id INTEGER,
    link_type TEXT DEFAULT 'direct',
    context TEXT,
    strength REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_note_id) REFERENCES notes(id),
    FOREIGN KEY (to_note_id) REFERENCES notes(id)
);

-- Таблица тегов
CREATE TABLE tags (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    color TEXT,
    description TEXT
);

-- Связь заметок и тегов
CREATE TABLE note_tags (
    note_id INTEGER,
    tag_id INTEGER,
    PRIMARY KEY (note_id, tag_id),
    FOREIGN KEY (note_id) REFERENCES notes(id),
    FOREIGN KEY (tag_id) REFERENCES tags(id)
);

-- Концепции и ключевые слова
CREATE TABLE concepts (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    definition TEXT,
    embedding BLOB,
    frequency INTEGER DEFAULT 1
);

-- Связь заметок и концепций
CREATE TABLE note_concepts (
    note_id INTEGER,
    concept_id INTEGER,
    relevance REAL DEFAULT 1.0,
    PRIMARY KEY (note_id, concept_id)
);
```

### Формат конфигурации

```yaml
# obsidian_mcp_config.yaml
vault:
  path: "/path/to/obsidian/vault"
  templates_folder: "Templates"
  daily_notes_folder: "Daily Notes"
  attachments_folder: "Attachments"

ai:
  embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
  similarity_threshold: 0.7
  max_suggestions: 5
  auto_link: true

organization:
  auto_tag: true
  create_mocs: true
  max_folder_depth: 3
  orphan_handling: "suggest_links"

monitoring:
  watch_changes: true
  auto_backup: true
  index_frequency: "daily"
```

## 🚀 Примеры использования

### Сценарий 1: Создание заметки с автоматическим связыванием

```python
# Пользователь просит: "Создай заметку о машинном обучении"
await mcp_client.call_tool("create_note", {
    "title": "Машинное обучение",
    "content": """# Машинное обучение

## Определение
Машинное обучение — это подраздел искусственного интеллекта...

## Типы обучения
- [[Обучение с учителем]]
- [[Обучение без учителя]] 
- [[Обучение с подкреплением]]

## Алгоритмы
- [[Линейная регрессия]]
- [[Случайный лес]]
- [[Нейронные сети]]

#машинное-обучение #ии #алгоритмы
    """,
    "tags": ["машинное-обучение", "ии", "алгоритмы"],
    "folder": "Технологии/ИИ"
})

# Автоматический анализ связей
await mcp_client.call_tool("analyze_connections", {
    "note_title": "Машинное обучение",
    "suggest_new": True
})
```

### Сценарий 2: Семантический поиск и организация

```python
# Поиск связанных концепций
results = await mcp_client.call_tool("semantic_search", {
    "query": "алгоритмы классификации данных",
    "limit": 5,
    "include_content": True
})

# Автоматическая организация найденных заметок
await mcp_client.call_tool("auto_organize", {
    "scope": "unorganized",
    "create_mocs": True,
    "min_cluster_size": 2
})
```

### Сценарий 3: Создание карты знаний

```python
# Получение карты знаний вокруг концепции
knowledge_map = await mcp_client.call_tool("get_knowledge_map", {
    "center_note": "Машинное обучение",
    "radius": 2,
    "cluster_by": "topic"
})

# Результат: граф с кластерами по темам
{
    "center": "Машинное обучение",
    "clusters": {
        "Алгоритмы": ["Линейная регрессия", "SVM", "Случайный лес"],
        "Типы обучения": ["Supervised Learning", "Unsupervised Learning"],
        "Применения": ["Computer Vision", "NLP", "Рекомендательные системы"]
    },
    "connections": [
        {"from": "Машинное обучение", "to": "Линейная регрессия", "strength": 0.8},
        {"from": "Supervised Learning", "to": "Линейная регрессия", "strength": 0.9}
    ]
}
```

## 🔄 Алгоритмы интеллектуальной обработки

### 1. Алгоритм создания связей

```python
async def suggest_links(note_title: str, content: str) -> List[LinkSuggestion]:
    """
    Алгоритм предложения связей на основе:
    1. Семантической схожести
    2. Общих ключевых слов
    3. Цитирований и упоминаний
    4. Временной близости создания
    """
    
    # Получаем эмбеддинг новой заметки
    note_embedding = get_embedding(content)
    
    # Поиск семантически похожих заметок
    similar_notes = find_similar_notes(note_embedding, threshold=0.7)
    
    # Извлечение упомянутых концепций
    mentioned_concepts = extract_concepts(content)
    
    # Поиск заметок с общими концепциями
    concept_related = find_notes_by_concepts(mentioned_concepts)
    
    # Объединение и ранжирование предложений
    suggestions = rank_suggestions(similar_notes + concept_related)
    
    return suggestions
```

### 2. Алгоритм кластеризации заметок

```python
async def cluster_notes(notes: List[Note]) -> Dict[str, List[Note]]:
    """
    Кластеризация заметок по темам:
    1. Векторизация содержимого
    2. Кластеризация методом K-means
    3. Автоматическое именование кластеров
    4. Создание MOC заметок
    """
    
    # Получаем эмбеддинги всех заметок
    embeddings = [note.embedding for note in notes]
    
    # Определяем оптимальное количество кластеров
    n_clusters = determine_optimal_clusters(embeddings)
    
    # Кластеризация
    clusters = kmeans_clustering(embeddings, n_clusters)
    
    # Именование кластеров по ключевым словам
    named_clusters = {}
    for i, cluster in enumerate(clusters):
        cluster_notes = [notes[idx] for idx in cluster]
        cluster_name = generate_cluster_name(cluster_notes)
        named_clusters[cluster_name] = cluster_notes
    
    return named_clusters
```

### 3. Система рекомендаций

```python
async def recommend_content(user_context: str, recent_notes: List[Note]) -> List[Recommendation]:
    """
    Система рекомендаций контента:
    1. Анализ интересов пользователя
    2. Поиск пробелов в знаниях
    3. Предложение новых тем для изучения
    4. Рекомендации по улучшению существующих заметок
    """
    
    # Анализ паттернов пользователя
    user_interests = analyze_user_patterns(recent_notes)
    
    # Поиск недостающих связей
    missing_links = find_missing_connections(recent_notes)
    
    # Генерация рекомендаций
    recommendations = []
    
    # Рекомендации новых тем
    for interest in user_interests:
        related_topics = find_related_topics(interest)
        recommendations.extend(create_topic_recommendations(related_topics))
    
    # Рекомендации улучшений
    for link in missing_links:
        recommendations.append(create_link_recommendation(link))
    
    return sorted(recommendations, key=lambda x: x.relevance_score, reverse=True)
```

## 📈 Метрики и аналитика

### Ключевые показатели системы

1. **Связность графа знаний**
   - Количество связей на заметку
   - Процент изолированных заметок
   - Средняя глубина связей

2. **Качество организации**
   - Точность автоматической кластеризации
   - Релевантность предлагаемых связей
   - Скорость поиска информации

3. **Активность использования**
   - Количество создаваемых заметок
   - Частота использования поиска
   - Принятие рекомендаций ИИ

### Dashboard метрик

```python
async def get_analytics_dashboard() -> Dict:
    """Получение дашборда аналитики vault'а"""
    return {
        "total_notes": await count_notes(),
        "total_links": await count_links(),
        "orphaned_notes": await count_orphaned_notes(),
        "top_tags": await get_top_tags(limit=10),
        "knowledge_clusters": await get_cluster_summary(),
        "growth_metrics": {
            "notes_this_week": await count_recent_notes(days=7),
            "links_created": await count_recent_links(days=7)
        },
        "ai_metrics": {
            "suggestions_made": await count_suggestions(),
            "suggestions_accepted": await count_accepted_suggestions(),
            "accuracy_rate": await calculate_suggestion_accuracy()
        }
    }
```

## 🛠️ План реализации

### Фаза 1: Базовая функциональность (2-3 недели)
- [ ] Настройка MCP сервера
- [ ] Базовые операции CRUD для заметок
- [ ] Простой поиск по заметкам
- [ ] Мониторинг файловой системы
- [ ] Базовая индексация содержимого

### Фаза 2: Интеллектуальные функции (3-4 недели)
- [ ] Семантическое сравнение заметок
- [ ] Автоматическое создание связей
- [ ] Извлечение ключевых концепций
- [ ] Система тегирования
- [ ] Базовая кластеризация

### Фаза 3: Продвинутые возможности (4-5 недель)
- [ ] Интеллектуальная организация vault'а
- [ ] Система рекомендаций
- [ ] Создание MOC заметок
- [ ] Расширенная аналитика
- [ ] API для внешних интеграций

### Фаза 4: Оптимизация и расширения (2-3 недели)
- [ ] Оптимизация производительности
- [ ] Продвинутые алгоритмы связывания
- [ ] Интеграция с внешними источниками
- [ ] Веб-интерфейс для управления
- [ ] Экспорт/импорт конфигураций

## 🔧 Технические детали реализации

### Структура проекта

```
obsidian-ai-mcp/
├── src/
│   ├── mcp_server/
│   │   ├── __init__.py
│   │   ├── server.py           # Основной MCP сервер
│   │   ├── tools.py            # Реализация MCP tools
│   │   └── handlers/
│   │       ├── notes.py        # Управление заметками
│   │       ├── links.py        # Управление связями
│   │       ├── search.py       # Поиск и индексация
│   │       └── analytics.py    # Аналитика
│   ├── ai/
│   │   ├── embeddings.py       # Векторизация текста
│   │   ├── clustering.py       # Кластеризация
│   │   ├── recommendations.py  # Система рекомендаций
│   │   └── nlp.py             # NLP обработка
│   ├── database/
│   │   ├── models.py          # Модели данных
│   │   ├── migrations.py      # Миграции БД
│   │   └── queries.py         # SQL запросы
│   └── utils/
│       ├── file_monitor.py    # Мониторинг файлов
│       ├── markdown_parser.py # Парсинг Markdown
│       └── config.py          # Конфигурация
├── tests/
├── examples/
├── docs/
├── requirements.txt
├── setup.py
└── README.md
```

### Основной entry point

```python
# src/mcp_server/server.py
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from .tools import register_tools
from .handlers import NotesHandler, LinksHandler, SearchHandler

app = Server("obsidian-ai-mcp")

async def main():
    """Запуск MCP сервера"""
    
    # Инициализация обработчиков
    notes_handler = NotesHandler(vault_path=VAULT_PATH)
    links_handler = LinksHandler(vault_path=VAULT_PATH)
    search_handler = SearchHandler(vault_path=VAULT_PATH)
    
    # Регистрация инструментов
    register_tools(app, notes_handler, links_handler, search_handler)
    
    # Запуск сервера
    async with stdio_server() as streams:
        await app.run(*streams)

if __name__ == "__main__":
    asyncio.run(main())
```

## 📖 Документация для пользователей

### Быстрый старт

1. **Установка**
```bash
pip install obsidian-ai-mcp
```

2. **Настройка**
```yaml
# config.yaml
vault_path: "/path/to/your/vault"
ai_model: "sentence-transformers/all-MiniLM-L6-v2"
```

3. **Запуск**
```bash
obsidian-ai-mcp --config config.yaml
```

### Примеры команд для Claude

```markdown
# Создание заметки с автоматическими связями
"Создай заметку о квантовых вычислениях с автоматическим связыванием"

# Анализ и организация vault'а  
"Проанализируй мой vault и предложи улучшения в организации"

# Поиск связанной информации
"Найди все заметки связанные с машинным обучением и покажи их связи"

# Создание карты знаний
"Создай карту знаний вокруг темы 'искусственный интеллект'"

# Автоматическая организация
"Автоматически организуй все неструктурированные заметки по папкам"
```

## 🚨 Важные соображения

### Безопасность и приватность
- Все данные остаются локально
- Опциональное шифрование индекса
- Контроль доступа к файлам vault'а
- Аудит всех изменений

### Производительность
- Инкрементальная индексация
- Кэширование эмбеддингов
- Ленивая загрузка больших файлов
- Оптимизация запросов к БД

### Совместимость
- Поддержка стандартного формата Obsidian
- Совместимость с существующими плагинами
- Возможность отключения ИИ-функций
- Экспорт в различные форматы

Этот проект создаст революционный опыт работы с базой знаний, где ИИ станет настоящим партнером в организации и структурировании информации!