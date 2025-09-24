#!/usr/bin/env python3
"""
Умная система поиска с индексацией содержимого для Obsidian MCP
Поддерживает многоязычный поиск, транслитерацию, морфологию
"""

import re
import sqlite3
import json
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
import hashlib
from datetime import datetime
import unicodedata
import logging

logger = logging.getLogger(__name__)


class SmartSearchEngine:
    """
    Умный поисковик для заметок Obsidian
    """
    
    def __init__(self, vault_path: Path, db_path: Optional[str] = None):
        self.vault_path = vault_path
        self.db_path = db_path or str(vault_path / ".obsidian" / "search_index.db")
        self.setup_database()
    
    def setup_database(self):
        """Настройка базы данных для индексации"""
        # Создаем папку если нужно
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        
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
        
        # Таблица инвертированного индекса
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS content_index (
                term TEXT,
                note_title TEXT,
                frequency INTEGER,
                positions TEXT,
                context TEXT,
                PRIMARY KEY (term, note_title)
            )
        """)
        
        # Индексы
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_content_term ON content_index(term)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_notes_modified ON notes(modified_date)")
        
        self.conn.commit()
    
    def search_notes(self, 
                     keywords: str = "",
                     search_in: str = "all",
                     
                     # Tag filters
                     include_tags = None,
                     exclude_tags = None, 
                     require_all_tags: bool = False,
                     
                     # Date filters
                     created_after = None,
                     created_before = None,
                     modified_after = None,
                     modified_before = None,
                     
                     # Folder filters
                     folders = None,
                     exclude_folders = None,
                     
                     # Content filters
                     min_words = None,
                     max_words = None,
                     has_tasks = None,
                     min_links = None,
                     max_links = None,
                     
                     # Search behavior
                     language_flexible: bool = True,
                     case_sensitive: bool = False,
                     fuzzy_matching: bool = True,
                     
                     # Results
                     limit: int = 20,
                     sort_by: str = "relevance",
                     include_content_preview: bool = True,
                     include_metadata: bool = True,
                     min_relevance: float = 0.1) -> Dict[str, Any]:
        """
        Главная функция умного поиска заметок с расширенными фильтрами
        """
        
        # Проверяем используются ли новые фильтры
        has_filters = any([
            include_tags, exclude_tags, created_after, created_before,
            modified_after, modified_before, folders, exclude_folders,
            min_words, max_words, has_tasks is not None, 
            min_links, max_links
        ])
        
        # Если есть фильтры, но методы не реализованы - fallback на старую логику
        if has_filters:
            # TODO: Implement filtering logic in Phase 2.1
            # For now, fallback to basic search with warning
            pass
        
        # Если нет ключевых слов - возвращаем последние заметки (старая логика)
        if not keywords.strip():
            return self._get_recent_notes(limit=limit, include_preview=include_content_preview)
        
        # Подготавливаем поисковые термы
        search_terms = self._prepare_search_terms(keywords, language_flexible, case_sensitive)
        
        # Обновляем индекс если нужно
        self._update_index_if_needed()
        
        # Выполняем поиск
        search_results = self._perform_search(
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
                "folder": self._get_folder_from_path(result["path"]),
                "relevance_score": round(result["relevance_score"], 3),
                "match_locations": result["match_locations"],
                "word_count": result["word_count"],
                "modified": result["modified"],
                "tags": result.get("tags", []),
                "link_count": result.get("link_count", 0)
            }
            
            # Добавляем превью содержимого
            if include_content_preview:
                note_data["content_preview"] = self._generate_content_preview(
                    result["path"], 
                    search_terms, 
                    max_chars=300
                )
                note_data["highlighted_matches"] = result["highlighted_matches"][:5]  # Топ-5 совпадений
            
            enriched_results.append(note_data)
        
        return {
            "search_query": keywords,
            "processed_terms": [t["original"] for t in search_terms],
            "total_found": len(search_results),
            "results": enriched_results,
            "search_stats": {
                "searched_in": search_in,
                "language_flexible": language_flexible,
                "case_sensitive": case_sensitive,
                "min_relevance": min_relevance
            },
            "suggestions": self._generate_search_suggestions(keywords) if len(search_results) < 3 else []
        }
    
    def _prepare_search_terms(self, keywords: str, language_flexible: bool, case_sensitive: bool) -> List[Dict]:
        """Подготавливает поисковые термы с учетом многоязычности"""
        terms = []
        
        # Обработка фраз в кавычках
        quoted_phrases = re.findall(r'"([^"]*)"', keywords)
        remaining_text = re.sub(r'"[^"]*"', '', keywords)
        
        # Добавляем фразы
        for phrase in quoted_phrases:
            if phrase.strip():
                terms.append({
                    "original": phrase.strip(),
                    "variants": self._generate_term_variants(phrase.strip(), language_flexible, case_sensitive),
                    "type": "phrase",
                    "weight": 2.0  # Фразы важнее
                })
        
        # Добавляем отдельные слова
        words = re.findall(r'\b\w+\b', remaining_text)
        for word in words:
            if len(word) > 1:
                terms.append({
                    "original": word,
                    "variants": self._generate_term_variants(word, language_flexible, case_sensitive),
                    "type": "word", 
                    "weight": 1.0
                })
        
        return terms
    
    def _generate_term_variants(self, term: str, language_flexible: bool, case_sensitive: bool) -> List[str]:
        """Генерирует варианты термина для гибкого поиска"""
        variants = [term]
        
        # Варианты регистра
        if not case_sensitive:
            variants.extend([term.lower(), term.upper(), term.capitalize()])
        
        if language_flexible:
            # Нормализация Unicode
            normalized = unicodedata.normalize('NFKD', term)
            variants.append(normalized)
            
            # Транслитерация
            variants.extend(self._generate_transliteration_variants(term))
            
            # Простые морфологические варианты
            variants.extend(self._generate_morphological_variants(term))
        
        # Убираем дубликаты и пустые строки
        return list(set(v for v in variants if v.strip()))
    
    def _generate_transliteration_variants(self, term: str) -> List[str]:
        """Генерирует варианты транслитерации русский <-> латиница"""
        variants = []
        
        # Карты транслитерации
        rus_to_lat = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'h', 'ц': 'c', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
            'ы': 'y', 'э': 'e', 'ю': 'yu', 'я': 'ya'
        }
        
        # Обратная карта
        lat_to_rus = {v: k for k, v in rus_to_lat.items()}
        lat_to_rus.update({
            'zh': 'ж', 'ch': 'ч', 'sh': 'ш', 'sch': 'щ', 'yu': 'ю', 'ya': 'я'
        })
        
        # Русский -> Латиница
        if any(c in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя' for c in term.lower()):
            transliterated = ''
            for char in term.lower():
                transliterated += rus_to_lat.get(char, char)
            
            if transliterated != term.lower():
                variants.append(transliterated)
                if term[0].isupper():
                    variants.append(transliterated.capitalize())
        
        # Латиница -> Русский (базово)
        else:
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
    
    def _generate_morphological_variants(self, term: str) -> List[str]:
        """Генерирует простые морфологические варианты"""
        variants = []
        
        # Распространенные окончания
        rus_endings = ['ть', 'сь', 'ся', 'ие', 'ый', 'ая', 'ое', 'ые', 'ов', 'ам', 'ами', 'ах', 'ем', 'ет']
        eng_endings = ['ing', 'ed', 'er', 'est', 'ly', 's', 'es', 'tion', 'sion']
        
        for endings in [rus_endings, eng_endings]:
            for ending in endings:
                if term.lower().endswith(ending) and len(term) > len(ending) + 2:
                    root = term[:-len(ending)]
                    if root:
                        variants.append(root)
                        variants.append(root.capitalize())
        
        return variants
    
    def _get_recent_notes(self, limit: int = 20, include_preview: bool = True) -> Dict[str, Any]:
        """Возвращает последние измененные заметки"""
        try:
            from .utils.vault import list_note_paths
            
            all_paths = []
            for path in list_note_paths(self.vault_path):
                if path.exists():
                    mtime = path.stat().st_mtime
                    all_paths.append((path, mtime))
            
            # Сортируем по времени изменения
            sorted_paths = sorted(all_paths, key=lambda x: x[1], reverse=True)
            
            results = []
            for path, mtime in sorted_paths[:limit]:
                result = {
                    "title": path.stem,
                    "path": str(path.relative_to(self.vault_path)),
                    "folder": self._get_folder_from_path(str(path.relative_to(self.vault_path))),
                    "modified": datetime.fromtimestamp(mtime).isoformat(),
                    "relevance_score": 1.0,
                    "match_locations": ["recent"],
                    "highlighted_matches": []
                }
                
                if include_preview:
                    result["content_preview"] = self._get_content_snippet(path, 200)
                
                results.append(result)
            
            return {
                "search_query": "",
                "processed_terms": [],
                "total_found": len(results),
                "results": results,
                "search_stats": {"type": "recent_notes"},
                "suggestions": []
            }
            
        except Exception as e:
            logger.error(f"Error getting recent notes: {e}")
            return {"search_query": "", "results": [], "total_found": 0, "error": str(e)}
    
    def _update_index_if_needed(self):
        """Обновляет индекс если есть новые/измененные файлы"""
        try:
            from .utils.vault import list_note_paths
            
            updated_count = 0
            for note_path in list_note_paths(self.vault_path):
                if self._needs_reindexing(note_path):
                    if self._index_note(note_path):
                        updated_count += 1
                        
            if updated_count > 0:
                logger.info(f"Updated search index for {updated_count} notes")
                
        except Exception as e:
            logger.warning(f"Error updating search index: {e}")
    
    def _needs_reindexing(self, note_path: Path) -> bool:
        """Проверяет нужность переиндексации"""
        if not note_path.exists():
            return False
            
        current_hash = self._calculate_content_hash(note_path)
        
        cursor = self.conn.execute(
            "SELECT content_hash FROM notes WHERE path = ?", 
            (str(note_path.relative_to(self.vault_path)),)
        )
        row = cursor.fetchone()
        
        return row is None or row[0] != current_hash
    
    def _index_note(self, note_path: Path) -> bool:
        """Индексирует заметку"""
        try:
            content = note_path.read_text(encoding='utf-8')
            title = note_path.stem
            relative_path = str(note_path.relative_to(self.vault_path))
            
            # Извлекаем метаданные
            metadata = self._extract_metadata(content, note_path)
            
            # Сохраняем метаданные
            self.conn.execute("""
                INSERT OR REPLACE INTO notes 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                title, relative_path, metadata['folder'], 
                metadata['word_count'], metadata['created'], metadata['modified'],
                metadata['content_hash'], json.dumps(metadata['tags']),
                json.dumps(metadata['links']), datetime.now().isoformat()
            ))
            
            # Удаляем старый контент индекс
            self.conn.execute("DELETE FROM content_index WHERE note_title = ?", (title,))
            
            # Индексируем содержимое
            self._index_content(title, content)
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error indexing {note_path}: {e}")
            return False
    
    def _index_content(self, note_title: str, content: str):
        """Индексирует содержимое заметки"""
        # Удаляем markdown разметку
        cleaned_content = re.sub(r'[#*`\[\]()]', ' ', content)
        
        # Извлекаем слова с позициями
        words = re.findall(r'\b\w+\b', cleaned_content.lower())
        term_positions = {}
        
        for i, word in enumerate(words):
            if len(word) > 2:  # Игнорируем короткие слова
                if word not in term_positions:
                    term_positions[word] = []
                term_positions[word].append(i)
        
        # Сохраняем в индекс
        for term, positions in term_positions.items():
            self.conn.execute("""
                INSERT OR REPLACE INTO content_index 
                VALUES (?, ?, ?, ?, ?)
            """, (
                term,
                note_title,
                len(positions),
                json.dumps(positions),
                "content"
            ))
    
    def _perform_search(self, search_terms: List[Dict], search_in: str, limit: int, min_relevance: float) -> List[Dict]:
        """Выполняет поиск в индексе"""
        results = {}  # note_title -> result_data
        
        for term_data in search_terms:
            for variant in term_data["variants"]:
                variant_lower = variant.lower()
                
                # Поиск в названиях
                if search_in in ["all", "titles"]:
                    cursor = self.conn.execute("""
                        SELECT title, path, word_count, modified_date, tags
                        FROM notes 
                        WHERE LOWER(title) LIKE ?
                        ORDER BY modified_date DESC
                        LIMIT ?
                    """, (f'%{variant_lower}%', limit))
                    
                    for row in cursor.fetchall():
                        title = row[0]
                        if title not in results:
                            results[title] = self._init_result_data(row)
                        
                        # Увеличиваем релевантность для совпадений в заголовке
                        results[title]['relevance_score'] += term_data['weight'] * 2.0
                        results[title]['match_locations'].append('title')
                        results[title]['highlighted_matches'].append(variant)
                
                # Поиск в содержимом
                if search_in in ["all", "content"]:
                    cursor = self.conn.execute("""
                        SELECT ci.note_title, ci.frequency, n.path, n.word_count, 
                               n.modified_date, n.tags
                        FROM content_index ci
                        JOIN notes n ON ci.note_title = n.title
                        WHERE ci.term = ?
                        ORDER BY ci.frequency DESC
                    """, (variant_lower,))
                    
                    for row in cursor.fetchall():
                        title = row[0]
                        frequency = row[1]
                        
                        if title not in results:
                            results[title] = self._init_result_data((title, row[2], row[3], row[4], row[5]))
                        
                        # Увеличиваем релевантность
                        results[title]['relevance_score'] += frequency * term_data['weight'] / 10.0
                        results[title]['match_locations'].append('content')
                        results[title]['highlighted_matches'].append(variant)
        
        # Фильтруем по минимальной релевантности
        filtered_results = [r for r in results.values() if r['relevance_score'] >= min_relevance]
        
        return sorted(filtered_results, key=lambda x: x['relevance_score'], reverse=True)
    
    def _init_result_data(self, row: Tuple) -> Dict:
        """Инициализирует данные результата поиска"""
        return {
            'title': row[0],
            'path': row[1],
            'word_count': row[2] if len(row) > 2 else 0,
            'modified': row[3] if len(row) > 3 else "",
            'tags': json.loads(row[4]) if len(row) > 4 and row[4] else [],
            'relevance_score': 0.0,
            'match_locations': [],
            'highlighted_matches': []
        }
    
    def _generate_content_preview(self, note_path: str, search_terms: List[Dict], max_chars: int = 300) -> str:
        """Генерирует превью содержимого с подсветкой"""
        try:
            full_path = self.vault_path / note_path
            content = full_path.read_text(encoding='utf-8')
            
            # Собираем все варианты терминов
            all_variants = []
            for term_data in search_terms:
                all_variants.extend(term_data['variants'])
            
            # Ищем лучший фрагмент
            best_fragment = self._find_best_fragment(content, all_variants, max_chars)
            
            if best_fragment:
                return self._highlight_terms(best_fragment, all_variants)
            else:
                return content[:max_chars] + "..." if len(content) > max_chars else content
                
        except Exception as e:
            return f"Ошибка чтения содержимого: {e}"
    
    def _find_best_fragment(self, content: str, variants: List[str], max_chars: int) -> str:
        """Находит лучший фрагмент с максимальным количеством совпадений"""
        sentences = re.split(r'[.!?\n]+', content)
        best_fragment = ""
        max_matches = 0
        
        for i, sentence in enumerate(sentences):
            # Берем несколько соседних предложений
            fragment_sentences = sentences[i:i+3]
            fragment = '. '.join(s.strip() for s in fragment_sentences if s.strip())
            
            if len(fragment) > max_chars:
                fragment = fragment[:max_chars] + "..."
            
            # Считаем совпадения
            matches = sum(1 for variant in variants 
                         if variant.lower() in fragment.lower())
            
            if matches > max_matches:
                max_matches = matches
                best_fragment = fragment
        
        return best_fragment
    
    def _highlight_terms(self, text: str, variants: List[str]) -> str:
        """Подсвечивает термины в тексте"""
        for variant in variants:
            if len(variant) > 1:
                pattern = re.compile(re.escape(variant), re.IGNORECASE)
                text = pattern.sub(f"**{variant}**", text)
        
        return text
    
    def _get_content_snippet(self, path: Path, max_chars: int) -> str:
        """Получает краткий отрывок содержимого"""
        try:
            content = path.read_text(encoding='utf-8')
            # Убираем frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    content = parts[2].strip()
            
            snippet = content[:max_chars].strip()
            return snippet + "..." if len(content) > max_chars else snippet
            
        except Exception as e:
            return f"Ошибка чтения: {e}"
    
    def _generate_search_suggestions(self, original_query: str) -> List[str]:
        """Генерирует предложения по улучшению поиска"""
        suggestions = []
        
        # Предлагаем более короткие варианты
        words = original_query.split()
        if len(words) > 1:
            suggestions.append(words[0])  # Первое слово
            if len(words) > 2:
                suggestions.append(' '.join(words[:2]))  # Первые два слова
        
        # Предлагаем транслитерацию
        if any(c in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя' for c in original_query.lower()):
            transliterated_variants = self._generate_transliteration_variants(original_query)
            suggestions.extend(transliterated_variants[:2])
        
        return suggestions[:3]
    
    def _get_folder_from_path(self, path: str) -> str:
        """Извлекает папку из пути"""
        path_obj = Path(path)
        return path_obj.parent.name if path_obj.parent.name != '.' else ""
    
    def _calculate_content_hash(self, note_path: Path) -> str:
        """Вычисляет хеш содержимого"""
        return hashlib.md5(note_path.read_bytes()).hexdigest()
    
    def _extract_metadata(self, content: str, note_path: Path) -> Dict:
        """Извлекает метаданные из заметки"""
        stat = note_path.stat()
        
        # Извлекаем теги
        tags = re.findall(r'#(\w+)', content)
        
        # Извлекаем ссылки
        links = re.findall(r'\[\[([^\]]+)\]\]', content)
        
        return {
            'folder': note_path.parent.name if note_path.parent != self.vault_path else "",
            'word_count': len(content.split()),
            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'content_hash': self._calculate_content_hash(note_path),
            'tags': tags,
            'links': links
        }
