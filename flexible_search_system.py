# Гибкая система поиска с индексацией содержимого

import re
import sqlite3
import json
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import hashlib
from datetime import datetime
import unicodedata

## 1. ОСНОВНАЯ ФУНКЦИЯ ПОИСКА (замена list_notes)

@server.call_tool()
async def search_notes(
    keywords: str = "",  # Ключевые слова для поиска
    search_in: str = "all",  # "titles", "content", "all"
    language_flexible: bool = True,  # Гибкий поиск по языкам
    case_sensitive: bool = False,  # Учет регистра
    limit: int = 20,  # Ограничение результатов
    include_content_preview: bool = True,  # Включать превью содержимого
    min_relevance: float = 0.1  # Минимальная релевантность (0-1)
) -> Dict:
    """
    Гибкий поиск заметок по ключевым словам с индексацией содержимого
    Заменяет простой list_notes для работы с большими vault'ами
    """
    
    # Если нет ключевых слов - возвращаем последние измененные заметки
    if not keywords.strip():
        return get_recent_notes(limit=limit, include_preview=include_content_preview)
    
    # Подготавливаем поисковые термы
    search_terms = prepare_search_terms(keywords, language_flexible, case_sensitive)
    
    # Выполняем поиск через индекс
    search_results = perform_indexed_search(
        search_terms=search_terms,
        search_in=search_in,
        limit=limit * 2,  # Берем больше для фильтрации
        min_relevance=min_relevance
    )
    
    # Обогащаем результаты
    enriched_results = []
    for result in search_results[:limit]:
        note_data = {
            "title": result["title"],
            "path": result["path"],
            "folder": get_folder_from_path(result["path"]),
            "relevance_score": result["relevance_score"],
            "match_locations": result["match_locations"],  # Где найдено совпадение
            "word_count": result["word_count"],
            "modified": result["modified"],
            "tags": result.get("tags", []),
            "link_count": result.get("link_count", 0)
        }
        
        # Добавляем превью содержимого с подсветкой найденных терминов
        if include_content_preview:
            note_data["content_preview"] = generate_content_preview(
                result["path"], 
                search_terms, 
                max_chars=300
            )
            note_data["highlighted_matches"] = result["highlighted_matches"]
        
        enriched_results.append(note_data)
    
    return {
        "search_query": keywords,
        "processed_terms": search_terms,
        "total_found": len(search_results),
        "results": enriched_results,
        "search_stats": {
            "searched_in": search_in,
            "language_flexible": language_flexible,
            "case_sensitive": case_sensitive,
            "min_relevance": min_relevance
        },
        "suggestions": generate_search_suggestions(keywords, search_results) if len(search_results) < 5 else []
    }

## 2. СИСТЕМА ПОДГОТОВКИ ПОИСКОВЫХ ТЕРМИНОВ

def prepare_search_terms(keywords: str, language_flexible: bool, case_sensitive: bool) -> List[Dict]:
    """
    Подготавливает поисковые термы с учетом многоязычности и регистра
    """
    # Разбиваем на отдельные слова и фразы
    terms = []
    
    # Обработка фраз в кавычках
    quoted_phrases = re.findall(r'"([^"]*)"', keywords)
    remaining_text = re.sub(r'"[^"]*"', '', keywords)
    
    # Добавляем фразы
    for phrase in quoted_phrases:
        if phrase.strip():
            terms.append({
                "original": phrase.strip(),
                "variants": generate_term_variants(phrase.strip(), language_flexible, case_sensitive),
                "type": "phrase",
                "weight": 2.0  # Фразы важнее
            })
    
    # Добавляем отдельные слова
    words = re.findall(r'\S+', remaining_text)
    for word in words:
        if len(word) > 1:  # Игнорируем слишком короткие слова
            terms.append({
                "original": word,
                "variants": generate_term_variants(word, language_flexible, case_sensitive),
                "type": "word",
                "weight": 1.0
            })
    
    return terms

def generate_term_variants(term: str, language_flexible: bool, case_sensitive: bool) -> List[str]:
    """
    Генерирует варианты термина для гибкого поиска
    """
    variants = [term]
    
    if not case_sensitive:
        variants.extend([term.lower(), term.upper(), term.capitalize()])
    
    if language_flexible:
        # Нормализация Unicode (для разных языков)
        normalized = unicodedata.normalize('NFKD', term)
        variants.append(normalized)
        
        # Транслитерация (русский <-> латиница)
        variants.extend(generate_transliteration_variants(term))
        
        # Морфологические варианты (базовые формы)
        variants.extend(generate_morphological_variants(term))
    
    # Убираем дубликаты и пустые строки
    return list(set(v for v in variants if v.strip()))

def generate_transliteration_variants(term: str) -> List[str]:
    """
    Генерирует варианты транслитерации
    """
    variants = []
    
    # Русский -> Латиница
    rus_to_lat = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'c', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ы': 'y', 'э': 'e', 'ю': 'yu', 'я': 'ya'
    }
    
    # Латиница -> Русский (обратная транслитерация)
    lat_to_rus = {v: k for k, v in rus_to_lat.items()}
    lat_to_rus.update({
        'zh': 'ж', 'ch': 'ч', 'sh': 'ш', 'sch': 'щ', 'yu': 'ю', 'ya': 'я'
    })
    
    # Пробуем транслитерировать
    if any(c in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя' for c in term.lower()):
        # Русский термин -> латиница
        transliterated = ''
        i = 0
        while i < len(term.lower()):
            found = False
            # Проверяем двухбуквенные сочетания
            if i < len(term) - 1:
                two_char = term.lower()[i:i+2]
                if two_char in ['дж', 'кс']:
                    transliterated += 'dj' if two_char == 'дж' else 'x'
                    i += 2
                    found = True
            
            if not found:
                char = term.lower()[i]
                transliterated += rus_to_lat.get(char, char)
                i += 1
                
        if transliterated != term.lower():
            variants.append(transliterated)
            if term[0].isupper():
                variants.append(transliterated.capitalize())
    
    else:
        # Латинский термин -> кириллица (упрощенно)
        term_lower = term.lower()
        for lat_seq, rus_char in sorted(lat_to_rus.items(), key=lambda x: len(x[0]), reverse=True):
            if lat_seq in term_lower:
                transliterated = term_lower.replace(lat_seq, rus_char)
                if transliterated != term_lower:
                    variants.append(transliterated)
                    if term[0].isupper():
                        variants.append(transliterated.capitalize())
                break
    
    return variants

def generate_morphological_variants(term: str) -> List[str]:
    """
    Генерирует базовые морфологические варианты (упрощенно)
    """
    variants = []
    
    # Русские окончания
    rus_endings = ['ть', 'сь', 'ся', 'ие', 'ый', 'ая', 'ое', 'ые', 'ов', 'ам', 'ами', 'ах']
    
    # Английские окончания  
    eng_endings = ['ing', 'ed', 'er', 'est', 'ly', 's', 'es']
    
    for endings in [rus_endings, eng_endings]:
        for ending in endings:
            if term.lower().endswith(ending) and len(term) > len(ending) + 2:
                root = term[:-len(ending)]
                if root:
                    variants.append(root)
    
    return variants

## 3. ИНДЕКСНАЯ СИСТЕМА

class ContentIndexer:
    """
    Система индексации содержимого заметок для быстрого поиска
    """
    
    def __init__(self, vault_path: str, db_path: str = "content_index.db"):
        self.vault_path = Path(vault_path)
        self.db_path = db_path
        self.setup_database()
    
    def setup_database(self):
        """Настройка базы данных для индексации"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA journal_mode=WAL")  # Для производительности
        
        # Таблица метаданных заметок
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                title TEXT PRIMARY KEY,
                path TEXT UNIQUE,
                folder TEXT,
                word_count INTEGER,
                created_date TEXT,
                modified_date TEXT,
                content_hash TEXT,
                tags TEXT,
                outgoing_links TEXT,
                indexed_at TEXT
            )
        """)
        
        # Таблица индекса содержимого (инвертированный индекс)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS content_index (
                term TEXT,
                note_title TEXT,
                frequency INTEGER,
                positions TEXT,  -- JSON массив позиций в тексте
                context TEXT,    -- heading, paragraph, list, etc.
                PRIMARY KEY (term, note_title)
            )
        """)
        
        # Индексы для быстрого поиска
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_content_term ON content_index(term)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_content_note ON content_index(note_title)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_notes_modified ON notes(modified_date)")
        
        self.conn.commit()
    
    def needs_reindexing(self, note_path: Path) -> bool:
        """Проверяет, нужно ли переиндексировать заметку"""
        if not note_path.exists():
            return False
            
        stat = note_path.stat()
        current_hash = self.calculate_content_hash(note_path)
        
        cursor = self.conn.execute(
            "SELECT content_hash FROM notes WHERE path = ?", 
            (str(note_path),)
        )
        row = cursor.fetchone()
        
        return row is None or row[0] != current_hash
    
    def index_note(self, note_path: Path) -> bool:
        """Индексирует отдельную заметку"""
        try:
            content = note_path.read_text(encoding='utf-8')
            title = note_path.stem
            
            # Извлекаем метаданные
            metadata = self.extract_metadata(content, note_path)
            
            # Сохраняем метаданные
            self.conn.execute("""
                INSERT OR REPLACE INTO notes 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                title, str(note_path), metadata['folder'], 
                metadata['word_count'], metadata['created'], metadata['modified'],
                metadata['content_hash'], json.dumps(metadata['tags']),
                json.dumps(metadata['links']), datetime.now().isoformat()
            ))
            
            # Удаляем старый индекс содержимого
            self.conn.execute("DELETE FROM content_index WHERE note_title = ?", (title,))
            
            # Индексируем содержимое
            self.index_content(title, content)
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"Ошибка индексации {note_path}: {e}")
            return False
    
    def index_content(self, note_title: str, content: str):
        """Индексирует содержимое заметки"""
        
        # Разбиваем контент на секции
        sections = self.parse_content_sections(content)
        
        for section in sections:
            # Извлекаем термы из секции
            terms = self.extract_terms(section['content'])
            
            for term, positions in terms.items():
                self.conn.execute("""
                    INSERT OR REPLACE INTO content_index 
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    term.lower(),
                    note_title,
                    len(positions),
                    json.dumps(positions),
                    section['type']
                ))
    
    def parse_content_sections(self, content: str) -> List[Dict]:
        """Разбирает контент на секции (заголовки, параграфы, списки)"""
        sections = []
        
        lines = content.split('\n')
        current_section = {'type': 'paragraph', 'content': '', 'line_start': 0}
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            if line_stripped.startswith('#'):
                # Заголовок
                if current_section['content'].strip():
                    sections.append(current_section)
                
                sections.append({
                    'type': 'heading',
                    'content': line_stripped,
                    'line_start': i,
                    'level': len(line_stripped.split()[0])
                })
                
                current_section = {'type': 'paragraph', 'content': '', 'line_start': i + 1}
                
            elif line_stripped.startswith(('- ', '* ', '+ ')) or re.match(r'\d+\. ', line_stripped):
                # Список
                if current_section['type'] != 'list':
                    if current_section['content'].strip():
                        sections.append(current_section)
                    current_section = {'type': 'list', 'content': '', 'line_start': i}
                
                current_section['content'] += line + '\n'
                
            else:
                # Обычный текст
                if current_section['type'] == 'list' and line_stripped:
                    if current_section['content'].strip():
                        sections.append(current_section)
                    current_section = {'type': 'paragraph', 'content': '', 'line_start': i}
                
                current_section['content'] += line + '\n'
        
        if current_section['content'].strip():
            sections.append(current_section)
        
        return sections
    
    def extract_terms(self, text: str) -> Dict[str, List[int]]:
        """Извлекает термы и их позиции из текста"""
        terms = {}
        
        # Удаляем markdown разметку
        cleaned_text = re.sub(r'[#*`\[\]()]', ' ', text)
        
        # Извлекаем слова
        words = re.findall(r'\b\w+\b', cleaned_text.lower())
        
        for i, word in enumerate(words):
            if len(word) > 2:  # Игнорируем короткие слова
                if word not in terms:
                    terms[word] = []
                terms[word].append(i)
        
        return terms
    
    def calculate_content_hash(self, note_path: Path) -> str:
        """Вычисляет хеш содержимого файла"""
        return hashlib.md5(note_path.read_bytes()).hexdigest()
    
    def extract_metadata(self, content: str, note_path: Path) -> Dict:
        """Извлекает метаданные из заметки"""
        stat = note_path.stat()
        
        # Извлекаем теги
        tags = re.findall(r'#(\w+)', content)
        
        # Извлекаем ссылки
        links = re.findall(r'\[\[([^\]]+)\]\]', content)
        
        return {
            'folder': note_path.parent.name,
            'word_count': len(content.split()),
            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'content_hash': self.calculate_content_hash(note_path),
            'tags': tags,
            'links': links
        }

## 4. ФУНКЦИЯ ПОИСКА ЧЕРЕЗ ИНДЕКС

def perform_indexed_search(
    search_terms: List[Dict],
    search_in: str,
    limit: int,
    min_relevance: float
) -> List[Dict]:
    """
    Выполняет поиск через индексированное содержимое
    """
    indexer = ContentIndexer(vault_path)
    
    # Собираем все варианты терминов
    all_variants = []
    for term_data in search_terms:
        all_variants.extend([
            (variant, term_data['weight'], term_data['type']) 
            for variant in term_data['variants']
        ])
    
    # Строим SQL запрос в зависимости от типа поиска
    if search_in == "titles":
        results = search_in_titles(indexer, all_variants, limit)
    elif search_in == "content":
        results = search_in_content(indexer, all_variants, limit)
    else:  # "all"
        title_results = search_in_titles(indexer, all_variants, limit // 2)
        content_results = search_in_content(indexer, all_variants, limit // 2)
        results = merge_search_results(title_results, content_results, limit)
    
    # Фильтруем по минимальной релевантности
    filtered_results = [r for r in results if r['relevance_score'] >= min_relevance]
    
    return sorted(filtered_results, key=lambda x: x['relevance_score'], reverse=True)

def search_in_titles(indexer: ContentIndexer, variants: List[Tuple], limit: int) -> List[Dict]:
    """Поиск в названиях заметок"""
    results = []
    
    for variant, weight, term_type in variants:
        cursor = indexer.conn.execute("""
            SELECT title, path, word_count, modified_date, tags
            FROM notes 
            WHERE LOWER(title) LIKE ?
            ORDER BY modified_date DESC
            LIMIT ?
        """, (f'%{variant.lower()}%', limit))
        
        for row in cursor.fetchall():
            results.append({
                'title': row[0],
                'path': row[1],
                'word_count': row[2],
                'modified': row[3],
                'tags': json.loads(row[4]) if row[4] else [],
                'relevance_score': calculate_title_relevance(row[0], variant, weight),
                'match_locations': ['title'],
                'highlighted_matches': [variant]
            })
    
    return results

def search_in_content(indexer: ContentIndexer, variants: List[Tuple], limit: int) -> List[Dict]:
    """Поиск в содержимом заметок"""
    results = {}  # note_title -> result_data
    
    for variant, weight, term_type in variants:
        cursor = indexer.conn.execute("""
            SELECT ci.note_title, ci.frequency, ci.context, n.path, n.word_count, 
                   n.modified_date, n.tags
            FROM content_index ci
            JOIN notes n ON ci.note_title = n.title
            WHERE ci.term = ?
            ORDER BY ci.frequency DESC
        """, (variant.lower(),))
        
        for row in cursor.fetchall():
            note_title = row[0]
            frequency = row[1]
            context = row[2]
            
            if note_title not in results:
                results[note_title] = {
                    'title': note_title,
                    'path': row[3],
                    'word_count': row[4],
                    'modified': row[5],
                    'tags': json.loads(row[6]) if row[6] else [],
                    'relevance_score': 0,
                    'match_locations': [],
                    'highlighted_matches': []
                }
            
            # Увеличиваем релевантность
            context_weight = {'heading': 2.0, 'list': 1.5, 'paragraph': 1.0}.get(context, 1.0)
            results[note_title]['relevance_score'] += frequency * weight * context_weight / 100
            results[note_title]['match_locations'].append(context)
            results[note_title]['highlighted_matches'].append(variant)
    
    return list(results.values())[:limit]

## 5. ФУНКЦИЯ ГЕНЕРАЦИИ ПРЕВЬЮ

def generate_content_preview(note_path: str, search_terms: List[Dict], max_chars: int = 300) -> str:
    """
    Генерирует превью содержимого с подсветкой найденных терминов
    """
    try:
        content = Path(note_path).read_text(encoding='utf-8')
        
        # Собираем все варианты терминов
        all_variants = []
        for term_data in search_terms:
            all_variants.extend(term_data['variants'])
        
        # Ищем лучший фрагмент
        best_fragment = find_best_content_fragment(content, all_variants, max_chars)
        
        if best_fragment:
            # Подсвечиваем найденные термины
            highlighted = highlight_terms_in_text(best_fragment, all_variants)
            return highlighted
        else:
            # Возвращаем начало содержимого
            return content[:max_chars] + "..." if len(content) > max_chars else content
            
    except Exception as e:
        return f"Ошибка чтения содержимого: {e}"

def find_best_content_fragment(content: str, search_variants: List[str], max_chars: int) -> str:
    """
    Находит наилучший фрагмент содержимого с максимальным количеством совпадений
    """
    sentences = re.split(r'[.!?]+', content)
    best_fragment = ""
    max_matches = 0
    
    for i, sentence in enumerate(sentences):
        # Берем несколько соседних предложений
        fragment_sentences = sentences[i:i+3]
        fragment = '. '.join(fragment_sentences).strip()
        
        if len(fragment) > max_chars:
            fragment = fragment[:max_chars] + "..."
        
        # Считаем количество совпадений
        matches = sum(1 for variant in search_variants 
                     if variant.lower() in fragment.lower())
        
        if matches > max_matches:
            max_matches = matches
            best_fragment = fragment
    
    return best_fragment

def highlight_terms_in_text(text: str, search_variants: List[str]) -> str:
    """
    Подсвечивает найденные термины в тексте
    """
    for variant in search_variants:
        # Используем регулярное выражение для выделения
        pattern = re.compile(re.escape(variant), re.IGNORECASE)
        text = pattern.sub(f"**{variant}**", text)
    
    return text