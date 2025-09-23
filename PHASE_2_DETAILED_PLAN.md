# 📋 Фаза 2: Семантический анализ - Детальный план реализации

## 🎯 Общая цель Фазы 2
Добавить к Enhanced MCP серверу возможности **семантического понимания** заметок с использованием машинного обучения для:
- Поиска похожих заметок по смыслу (не только по словам)
- Интеллектуального анализа связей между концепциями
- Контекстуального поиска с пониманием намерений пользователя

---

## 🛠️ Технический стек для реализации

### **Библиотеки ML/AI:**
```bash
# Основные зависимости для семантического анализа
pip install sentence-transformers>=2.2.2  # Embeddings моделей
pip install numpy>=1.24.0                # Векторные операции
pip install scikit-learn>=1.3.0          # Кластеризация и метрики
pip install spacy>=3.6.0                 # NLP обработка
pip install torch>=2.0.0                 # PyTorch для моделей

# Дополнительные языковые модели
python -m spacy download en_core_web_sm   # Английский
python -m spacy download ru_core_news_sm  # Русский (если доступен)
```

### **Модели для embeddings:**
- **sentence-transformers/all-MiniLM-L6-v2** (384 dim, 80MB) - быстрая и легкая
- **sentence-transformers/all-mpnet-base-v2** (768 dim, 420MB) - более точная
- **sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2** - для многоязычности

---

## 🏗️ Архитектура расширения

### **Новая структура проекта:**
```
src/obsidian_mcp/
├── server.py                    # [существующий] Основной сервер
├── smart_search.py              # [существующий] Текущий поиск
├── ai/                          # [НОВЫЙ] ИИ компоненты
│   ├── __init__.py
│   ├── embeddings.py            # Управление embeddings
│   ├── similarity.py            # Поиск похожих заметок
│   ├── contextual_search.py     # Контекстуальный поиск  
│   ├── connections.py           # Анализ связей
│   └── models.py                # Загрузка и кэширование моделей
├── database/                    # [НОВЫЙ] Расширенная БД
│   ├── __init__.py
│   ├── schema_v2.sql           # Новая схема с embeddings
│   ├── migrations.py           # Миграции существующей БД
│   └── vector_store.py         # Векторное хранилище
└── utils/                       # [существующие] Утилиты
```

---

## 📋 Детальный план реализации

### **🔧 Этап 2.1: Настройка AI инфраструктуры (1 неделя)**

#### **День 1-2: Установка зависимостей и базовая настройка**
```bash
# Задачи:
✓ Добавить ML зависимости в pyproject.toml
✓ Создать ai/ директорию с базовыми модулями
✓ Настроить загрузку и кэширование моделей
✓ Создать систему конфигурации для AI компонентов

# Файлы для создания:
- src/obsidian_mcp/ai/models.py
- src/obsidian_mcp/ai/__init__.py  
- ai_config.yaml (настройки моделей)
```

**models.py структура:**
```python
class EmbeddingManager:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.cache_dir = vault_path / ".obsidian" / "embeddings_cache"
    
    async def get_embedding(self, text: str) -> np.ndarray:
        # Кэширование embeddings по хешу текста
    
    async def batch_embed(self, texts: List[str]) -> np.ndarray:
        # Пакетная обработка для эффективности
```

#### **День 3-4: Расширение базы данных**
```sql
-- Новые таблицы в schema_v2.sql
CREATE TABLE note_embeddings (
    note_title TEXT PRIMARY KEY,
    embedding BLOB,              -- Сериализованный numpy array
    embedding_model TEXT,        -- Имя модели для совместимости
    content_hash TEXT,           -- Хеш содержимого для инвалидации
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE semantic_clusters (
    cluster_id INTEGER PRIMARY KEY,
    cluster_name TEXT,
    representative_notes TEXT,   -- JSON список репрезентативных заметок
    created_at TIMESTAMP
);

CREATE TABLE note_similarities (
    note1_title TEXT,
    note2_title TEXT, 
    similarity_score REAL,
    model_used TEXT,
    calculated_at TIMESTAMP,
    PRIMARY KEY (note1_title, note2_title)
);
```

#### **День 5-7: Миграция существующих данных**
```python
# database/migrations.py
async def migrate_to_v2():
    # Добавить новые таблицы
    # Создать embeddings для существующих заметок
    # Обновить smart_search.py для использования векторного поиска
```

### **🧠 Этап 2.2: Реализация семантического поиска (1-2 недели)**

#### **Неделя 1: find_similar_notes**
```python
@mcp.tool()
def find_similar_notes(
    ctx: Context[ServerSession, AppContext],
    reference_note: str,
    similarity_threshold: float = 0.7,
    limit: int = 10,
    include_scores: bool = True
) -> Dict[str, Any]:
    """
    🔍 FIND SIMILAR NOTES - Semantic similarity search
    
    PURPOSE: Find notes with similar meaning, not just similar words.
    Uses AI embeddings to understand semantic relationships.
    
    FEATURES:
    • Semantic understanding (finds "neural networks" when searching "deep learning")
    • Multilingual similarity (связанные заметки на разных языках)
    • Adjustable similarity threshold
    • Scored results with explanation
    
    USE CASES:
    • Research: "Find notes similar to my machine learning introduction"
    • Knowledge gaps: "What else do I have on this topic?"
    • Content connections: "Show related concepts to artificial intelligence"
    """
```

**Техническая реализация:**
```python
# ai/similarity.py
class NoteSimilarityAnalyzer:
    def __init__(self, embedding_manager, vector_store):
        self.embeddings = embedding_manager
        self.vector_store = vector_store
    
    async def find_similar(self, reference_note: str, threshold: float, limit: int):
        # 1. Получить embedding референсной заметки
        ref_embedding = await self.embeddings.get_note_embedding(reference_note)
        
        # 2. Поиск в векторном хранилище
        similar_embeddings = await self.vector_store.similarity_search(
            ref_embedding, threshold, limit
        )
        
        # 3. Ранжирование и форматирование результатов
        return self.format_similarity_results(similar_embeddings)
```

#### **Неделя 2: search_contextual**
```python
@mcp.tool() 
def search_contextual(
    ctx: Context[ServerSession, AppContext],
    query: str,
    context: Optional[str] = None,
    search_intent: str = "general",  # "research", "reference", "brainstorm"
    include_semantic: bool = True,
    limit: int = 15
) -> Dict[str, Any]:
    """
    🎯 CONTEXTUAL SEARCH - AI-powered search with intent understanding
    
    PURPOSE: Smart search that understands what you're trying to accomplish,
    not just matching keywords. Uses context and intent to find relevant notes.
    
    FEATURES:  
    • Intent recognition (research vs reference vs brainstorming)
    • Contextual understanding ("Python" means programming in tech context)
    • Semantic expansion (finds related concepts automatically)
    • Query reformulation for better results
    
    USE CASES:
    • Research mode: "Find technical details about React performance"
    • Reference mode: "Quick lookup of authentication patterns" 
    • Brainstorm mode: "Show me creative ideas related to user experience"
    """
```

### **🔗 Этап 2.3: Анализ связей (1 неделя)**

#### **analyze_note_connections**
```python
@mcp.tool()
def analyze_note_connections(
    ctx: Context[ServerSession, AppContext], 
    note_title: str,
    analysis_depth: int = 2,
    connection_threshold: float = 0.6,
    suggest_new_links: bool = True
) -> Dict[str, Any]:
    """
    🕸️ ANALYZE NOTE CONNECTIONS - Deep relationship analysis
    
    PURPOSE: Understand how a note fits into your knowledge graph.
    Discovers both explicit links and implicit semantic relationships.
    
    FEATURES:
    • Multi-level relationship analysis (direct, indirect, conceptual)
    • Gap detection (missing connections that should exist)
    • Cluster analysis (what conceptual groups this note belongs to)  
    • Link suggestions with confidence scores
    
    RETURNS:
    • Existing connections (explicit links)
    • Semantic connections (implicit relationships)
    • Missing connections (should be linked but aren't)
    • Conceptual clusters (thematic groups)
    • Actionable suggestions
    """
```

**Техническая реализация:**
```python
# ai/connections.py  
class ConnectionAnalyzer:
    async def analyze_connections(self, note_title: str, depth: int):
        # 1. Анализ существующих связей
        explicit_links = await self.get_explicit_links(note_title, depth)
        
        # 2. Семантический анализ связей
        semantic_connections = await self.find_semantic_connections(note_title)
        
        # 3. Кластерный анализ
        clusters = await self.analyze_clusters(note_title)
        
        # 4. Поиск пробелов в связях
        missing_links = await self.suggest_missing_links(note_title)
        
        return {
            "explicit_connections": explicit_links,
            "semantic_connections": semantic_connections, 
            "clusters": clusters,
            "suggested_links": missing_links,
            "analysis_metadata": {...}
        }
```

---

## 🗃️ Система векторного хранилища

### **Выбор векторной БД:**
```python
# Варианты реализации (по сложности):

# 1. ПРОСТОЙ: Расширение SQLite (рекомендуется для начала)
# Pros: Без дополнительных зависимостей, простая интеграция
# Cons: Менее эффективен для больших коллекций (>10k заметок)

# 2. СРЕДНИЙ: ChromaDB 
# Pros: Легкая интеграция, хорошая производительность
# Cons: Дополнительная зависимость

# 3. ПРОДВИНУТЫЙ: Pinecone/Weaviate
# Pros: Максимальная производительность, облачное решение
# Cons: Требует внешнего сервиса
```

### **Рекомендуемая реализация (SQLite + numpy):**
```python
# database/vector_store.py
class SQLiteVectorStore:
    def __init__(self, db_path: Path):
        self.conn = sqlite3.connect(db_path)
        
    async def store_embedding(self, note_title: str, embedding: np.ndarray):
        # Сериализация embedding в BLOB
        embedding_blob = embedding.tobytes()
        
    async def similarity_search(self, query_embedding: np.ndarray, threshold: float, limit: int):
        # Загрузка всех embeddings (для малых коллекций)
        # Вычисление cosine similarity с numpy
        # Фильтрация и ранжирование результатов
```

---

## 📊 Метрики производительности

### **Бенчмарки для тестирования:**
```python
# Цели производительности:
- Поиск в коллекции 1000 заметок: < 500ms
- Создание embedding новой заметки: < 200ms  
- Batch обработка 100 заметок: < 30s
- Размер индекса: < 50MB для 1000 заметок
- RAM использование: < 500MB при загруженной модели
```

### **Оптимизации:**
```python
# 1. Кэширование embeddings на диске
# 2. Lazy loading моделей (загружать только при использовании)
# 3. Batch обработка для новых заметок
# 4. Инкрементальное обновление индекса
# 5. Конфигурируемые модели (от быстрых до точных)
```

---

## 🧪 Тестирование Фазы 2

### **Тестовые сценарии:**
```python
# test_semantic_phase2.py
async def test_similarity_search():
    # 1. Создать заметки на похожие темы
    # 2. Проверить что find_similar_notes находит релевантные
    # 3. Проверить что similarity scores разумные (0.7+)
    
async def test_multilingual_similarity():
    # 1. Заметка на английском про "machine learning"
    # 2. Заметка на русском про "машинное обучение" 
    # 3. Проверить что они считаются похожими
    
async def test_contextual_search():
    # 1. Поиск "Python" в контексте programming
    # 2. Поиск "Python" в контексте animals
    # 3. Проверить что результаты отличаются по контексту
```

---

## ⚠️ Потенциальные сложности

### **1. Производительность:**
- **Проблема**: ML модели медленные, особенно на CPU
- **Решение**: Кэширование, batch обработка, опциональная GPU поддержка

### **2. Размер зависимостей:**
- **Проблема**: torch + transformers = 2-3GB зависимостей
- **Решение**: Опциональные зависимости, легкие модели, предупреждения

### **3. Многоязычность:**
- **Проблема**: Качество для русского языка может быть ниже
- **Решение**: Тестирование разных моделей, fallback на keyword поиск

### **4. Точность семантического поиска:**
- **Проблема**: AI может находить ложные связи
- **Решение**: Настраиваемые пороги, объяснения результатов

---

## 🎯 Критерии готовности Фазы 2

### **Обязательные функции:**
- ✅ `find_similar_notes` работает с точностью >80%
- ✅ `search_contextual` понимает базовый контекст  
- ✅ `analyze_note_connections` обнаруживает семантические связи
- ✅ Производительность соответствует бенчмаркам
- ✅ Все тесты проходят

### **Дополнительные функции:**
- 🔄 Многоязычная поддержка (русский + английский)
- 🔄 GPU ускорение (опционально)
- 🔄 Автоматическая кластеризация заметок
- 🔄 Интеграция с существующим explore_notes

---

## 💰 Оценка времени и ресурсов

### **Временные затраты:**
- **Этап 2.1** (Инфраструктура): 1 неделя (40 часов)
- **Этап 2.2** (Семантический поиск): 1-2 недели (40-80 часов)  
- **Этап 2.3** (Анализ связей): 1 неделя (40 часов)
- **Тестирование и оптимизация**: 1 неделя (40 часов)

**Общее время: 4-5 недель (160-200 часов)**

### **Технические требования:**
- **RAM**: 2-4GB для работы с моделями
- **Диск**: 3-5GB для зависимостей + модели  
- **CPU**: Рекомендуется 4+ ядер для разумной производительности
- **GPU**: Опционально, ускорит работу в 5-10 раз

---

## 🚀 Следующие шаги для начала Фазы 2

### **Немедленные действия:**
1. **Создать ветку**: `git checkout -b phase-2-semantic-analysis`
2. **Обновить pyproject.toml** с ML зависимостями
3. **Создать ai/ директорию** и базовые модули
4. **Настроить тестовую среду** с малыми моделями
5. **Реализовать models.py** для управления embeddings

### **Первая итерация (MVP):**
- Базовый `find_similar_notes` с all-MiniLM-L6-v2
- SQLite расширение для хранения embeddings  
- Простой тест на 10-20 заметках
- Интеграция с существующим obsidian-ai-mcp сервером

Готовы начать Фазу 2? 🚀
