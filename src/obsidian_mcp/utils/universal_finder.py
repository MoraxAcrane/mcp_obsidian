"""
🔍 Universal Note Finder

Система поиска заметок во всем vault для решения проблем с подпапками.
Заменяет ограниченный note_path_for_title на полнофункциональный поиск.
"""

from pathlib import Path
from typing import Optional, Dict, List, Tuple
import unicodedata
import re


class UniversalNoteFinder:
    """
    Универсальная система поиска заметок в vault.
    
    Решает проблемы:
    - Поиск только в корневой папке
    - Проблемы с эмодзи в названиях  
    - Дублирующиеся названия заметок
    - Нечувствительность к регистру
    """
    
    def __init__(self, vault_path: Path):
        self.vault_path = Path(vault_path)
        self.title_index = {}  # title -> path mapping
        self.path_index = {}   # path -> title mapping
        self._build_index()
    
    def _build_index(self):
        """Строим полный индекс всех заметок в vault"""
        self.title_index.clear()
        self.path_index.clear()
        
        # Сканируем все .md файлы рекурсивно
        for md_file in self.vault_path.rglob("*.md"):
            if not md_file.is_file():
                continue
                
            try:
                title = md_file.stem
                relative_path = md_file.relative_to(self.vault_path)
                
                # Нормализуем title для лучшего поиска
                normalized_title = self._normalize_title(title)
                
                # Обрабатываем дублирующиеся названия
                unique_key = self._create_unique_key(title, relative_path)
                
                # Сохраняем в индексы - ключи должны быть разные!
                self.title_index[title] = relative_path
                if normalized_title != title:  # Избегаем перезаписи
                    self.title_index[normalized_title] = relative_path
                if unique_key != title:  # Избегаем перезаписи
                    self.title_index[unique_key] = relative_path
                
                # Обратный индекс
                self.path_index[str(relative_path)] = title
                
            except Exception as e:
                # Пропускаем проблемные файлы, но не падаем
                continue
    
    def _normalize_title(self, title: str) -> str:
        """Нормализует название для лучшего поиска"""
        # Удаляем эмодзи и спец символы для альтернативного поиска
        normalized = unicodedata.normalize('NFKD', title)
        
        # Убираем эмодзи (но сохраняем оригинал тоже)
        emoji_pattern = re.compile(
            r'[\U0001F600-\U0001F64F]|'  # emoticons
            r'[\U0001F300-\U0001F5FF]|'  # symbols & pictographs
            r'[\U0001F680-\U0001F6FF]|'  # transport & map symbols
            r'[\U0001F1E0-\U0001F1FF]|'  # flags
            r'[\U00002702-\U000027B0]|'  # dingbats
            r'[\U000024C2-\U0001F251]'   # enclosed characters
        )
        
        no_emoji = emoji_pattern.sub('', title).strip()
        return no_emoji if no_emoji else title
    
    def _create_unique_key(self, title: str, path: Path) -> str:
        """Создает уникальный ключ для дублирующихся названий"""
        if path.parent == Path('.'):
            return title  # В корне
        
        folder = path.parent.name
        return f"{title} ({folder})"
    
    def find_note(self, title: str) -> Optional[Path]:
        """
        Находит заметку по названию в любой папке vault.
        
        Стратегии поиска:
        1. Точное совпадение
        2. Нормализованное совпадение (без эмодзи)
        3. Case-insensitive поиск
        4. Частичное совпадение
        5. Fuzzy matching
        """
        if not title:
            return None
        
        # 1. Точное совпадение
        if title in self.title_index:
            path = self.vault_path / self.title_index[title]
            if path.exists():
                return path
        
        # 2. Нормализованное совпадение
        normalized_title = self._normalize_title(title)
        if normalized_title != title and normalized_title in self.title_index:
            path = self.vault_path / self.title_index[normalized_title]
            if path.exists():
                return path
        
        # 3. Case-insensitive поиск
        title_lower = title.lower()
        for indexed_title, relative_path in self.title_index.items():
            if indexed_title.lower() == title_lower:
                path = self.vault_path / relative_path
                if path.exists():
                    return path
        
        # 4. Частичное совпадение (содержит подстроку)
        for indexed_title, relative_path in self.title_index.items():
            if title in indexed_title or indexed_title in title:
                path = self.vault_path / relative_path
                if path.exists():
                    return path
        
        # 5. Fuzzy matching для эмодзи и спец символов
        for indexed_title, relative_path in self.title_index.items():
            if self._fuzzy_match(title, indexed_title):
                path = self.vault_path / relative_path
                if path.exists():
                    return path
        return None
    
    def _fuzzy_match(self, title1: str, title2: str, threshold: float = 0.8) -> bool:
        """Нечеткое сравнение названий"""
        # Простая метрика схожести
        norm1 = self._normalize_title(title1).lower().strip()
        norm2 = self._normalize_title(title2).lower().strip()
        
        if not norm1 or not norm2:
            return False
        
        # Levenshtein distance approximation
        longer = norm1 if len(norm1) > len(norm2) else norm2
        shorter = norm2 if len(norm1) > len(norm2) else norm1
        
        if len(longer) == 0:
            return True
        
        # Простая метрика - процент совпадающих символов
        matches = sum(1 for a, b in zip(longer, shorter) if a == b)
        similarity = matches / len(longer)
        
        return similarity >= threshold
    
    def find_multiple(self, title: str, limit: int = 10) -> List[Tuple[str, Path]]:
        """Находит несколько заметок, подходящих под название"""
        results = []
        
        title_lower = title.lower()
        for indexed_title, relative_path in self.title_index.items():
            if (title_lower in indexed_title.lower() or 
                indexed_title.lower() in title_lower):
                
                full_path = self.vault_path / relative_path
                if full_path.exists():
                    results.append((indexed_title, full_path))
                    
                if len(results) >= limit:
                    break
        
        return results
    
    def get_all_notes(self) -> List[Tuple[str, Path]]:
        """Возвращает все заметки в vault"""
        results = []
        
        for title, relative_path in self.path_index.items():
            full_path = self.vault_path / relative_path
            if full_path.exists():
                results.append((self.path_index[title], full_path))
        
        return results
    
    def refresh_index(self, changed_files: Optional[List[Path]] = None):
        """Обновляет индекс (для real-time sync)"""
        if changed_files is None:
            # Полная переиндексация
            self._build_index()
        else:
            # Инкрементальное обновление
            for file_path in changed_files:
                try:
                    if file_path.suffix == '.md':
                        if file_path.exists():
                            # Файл изменен/создан
                            title = file_path.stem
                            relative_path = file_path.relative_to(self.vault_path)
                            normalized_title = self._normalize_title(title)
                            unique_key = self._create_unique_key(title, relative_path)
                            
                            self.title_index[title] = relative_path
                            self.title_index[normalized_title] = relative_path
                            self.title_index[unique_key] = relative_path
                            self.path_index[str(relative_path)] = title
                        else:
                            # Файл удален
                            relative_path = file_path.relative_to(self.vault_path)
                            title = self.path_index.get(str(relative_path))
                            
                            if title:
                                # Удаляем из индексов
                                self.title_index.pop(title, None)
                                self.title_index.pop(self._normalize_title(title), None)
                                self.path_index.pop(str(relative_path), None)
                                
                except Exception:
                    continue
    
    def get_stats(self) -> Dict:
        """Статистика индекса для debugging"""
        return {
            "total_notes": len(self.path_index),
            "indexed_titles": len(self.title_index),
            "vault_path": str(self.vault_path),
            "sample_titles": list(self.path_index.values())[:10]
        }


# Глобальный finder для кэширования (singleton pattern)
_finder_cache = {}

def get_universal_finder(vault_path: Path) -> UniversalNoteFinder:
    """Получить UniversalNoteFinder с кэшированием"""
    vault_str = str(vault_path)
    
    if vault_str not in _finder_cache:
        _finder_cache[vault_str] = UniversalNoteFinder(vault_path)
    
    return _finder_cache[vault_str]


def refresh_finder_cache(vault_path: Path, changed_files: Optional[List[Path]] = None):
    """Обновить кэш finder'а"""
    vault_str = str(vault_path)
    
    if vault_str in _finder_cache:
        _finder_cache[vault_str].refresh_index(changed_files)
    else:
        _finder_cache[vault_str] = UniversalNoteFinder(vault_path)
