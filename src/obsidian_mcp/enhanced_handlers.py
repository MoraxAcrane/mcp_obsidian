#!/usr/bin/env python3
"""
Enhanced handlers для MCP сервера Obsidian
Содержит обработчики всех расширенных инструментов
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from mcp.types import TextContent, CallToolResult

from .utils.markdown_parser import (
    extract_outlinks,
    read_note_frontmatter, 
    write_note_frontmatter,
)
from .utils.vault import list_note_paths, note_path_for_title


def get_note_metadata(path: Path, content: str) -> Dict[str, Any]:
    """Получение расширенных метаданных заметки"""
    try:
        stat = path.stat()
        
        # Подсчет статистики контента
        word_count = len(content.split())
        char_count = len(content)
        line_count = len(content.splitlines())
        
        # Анализ ссылок
        outlinks = extract_outlinks(content)
        link_count = len(outlinks)
        
        # Анализ тегов из контента
        tag_pattern = re.compile(r'#(\w+)')
        content_tags = list(set(tag_pattern.findall(content)))
        
        # Анализ заголовков
        heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        headings = [{"level": len(match.group(1)), "text": match.group(2).strip()} 
                   for match in heading_pattern.finditer(content)]
        
        return {
            "file_info": {
                "size_bytes": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "accessed": datetime.fromtimestamp(stat.st_atime).isoformat()
            },
            "content_stats": {
                "word_count": word_count,
                "char_count": char_count,
                "line_count": line_count,
                "link_count": link_count,
                "heading_count": len(headings),
                "tag_count": len(content_tags)
            },
            "structure": {
                "headings": headings[:10],  # Первые 10 заголовков
                "tags_in_content": content_tags,
                "outlinks": outlinks
            }
        }
    except Exception as e:
        return {"error": str(e)}


def analyze_vault_health(vault_path: Path) -> Dict[str, Any]:
    """Анализ здоровья и статистики vault"""
    try:
        all_notes = list(list_note_paths(vault_path))
        total_notes = len(all_notes)
        
        if total_notes == 0:
            return {"total_notes": 0, "message": "Vault is empty"}
        
        # Статистика размеров
        total_size = sum(path.stat().st_size for path in all_notes if path.exists())
        
        # Анализ связей
        all_links = []
        orphaned_notes = []
        notes_with_links = 0
        
        for note_path in all_notes:
            try:
                content, _ = read_note_frontmatter(note_path)
                outlinks = extract_outlinks(content)
                
                if outlinks:
                    all_links.extend(outlinks)
                    notes_with_links += 1
                else:
                    orphaned_notes.append(note_path.stem)
            except:
                continue
        
        # Анализ структуры папок
        folders = set()
        for note_path in all_notes:
            if note_path.parent != vault_path:
                rel_folder = note_path.parent.relative_to(vault_path)
                folders.add(str(rel_folder))
        
        return {
            "overview": {
                "total_notes": total_notes,
                "total_size_mb": round(total_size / 1024 / 1024, 2),
                "folders_count": len(folders),
                "notes_with_links": notes_with_links,
                "orphaned_notes_count": len(orphaned_notes)
            },
            "health_metrics": {
                "connectivity_ratio": round(notes_with_links / total_notes * 100, 1),
                "average_links_per_note": round(len(all_links) / total_notes, 2),
                "folder_organization": "good" if len(folders) > 0 else "needs_folders"
            },
            "top_folders": list(folders)[:10],
            "orphaned_notes": orphaned_notes[:20],  # Первые 20
            "most_linked": list(set(all_links))[:10]  # Самые популярные ссылки
        }
        
    except Exception as e:
        return {"error": str(e)}


# =============================================================================
# РАСШИРЕННЫЕ ОБРАБОТЧИКИ
# =============================================================================

async def handle_vault_overview(vault_path: Path, args: Dict[str, Any]) -> CallToolResult:
    """🏠 Комплексный анализ vault со статистикой и рекомендациями"""
    include_detailed_stats = args.get("include_detailed_stats", True)
    
    vault_stats = analyze_vault_health(vault_path)
    
    if include_detailed_stats and "health_metrics" in vault_stats:
        # Добавляем рекомендации на основе анализа
        recommendations = []
        
        connectivity = vault_stats["health_metrics"]["connectivity_ratio"]
        if connectivity < 20:
            recommendations.append("🔗 Low connectivity - consider linking related notes")
        elif connectivity > 80:
            recommendations.append("✅ Excellent connectivity - well-connected knowledge base")
        
        if vault_stats["overview"]["orphaned_notes_count"] > 5:
            recommendations.append("🏝️ Many orphaned notes - consider creating connections")
        
        if vault_stats["overview"]["folders_count"] == 0:
            recommendations.append("📁 No folder structure - consider organizing notes into folders")
        
        vault_stats["recommendations"] = recommendations
    
    result = {
        "tool": "vault_overview",
        "timestamp": datetime.now().isoformat(),
        "vault_analysis": vault_stats
    }
    
    return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))])


async def handle_read_note_enhanced(vault_path: Path, args: Dict[str, Any]) -> CallToolResult:
    """📖 Чтение заметки с расширенными метаданными"""
    title = args["title"]
    include_backlinks = args.get("include_backlinks", True)
    include_outlinks = args.get("include_outlinks", True)
    include_metadata = args.get("include_metadata", True)
    
    path = note_path_for_title(vault_path, title)
    if not path.exists():
        return CallToolResult(content=[TextContent(type="text", text=f"❌ Note not found: {title}")])
    
    content, frontmatter_metadata = read_note_frontmatter(path)
    
    result = {
        "tool": "read_note_enhanced",
        "title": title,
        "content": content,
        "frontmatter": frontmatter_metadata
    }
    
    # Расширенные метаданные
    if include_metadata:
        result["enhanced_metadata"] = get_note_metadata(path, content)
    
    # Анализ связей
    if include_outlinks:
        result["outlinks"] = extract_outlinks(content)
        
    if include_backlinks:
        backlinks = []
        needle = f"[[{title}]]"
        for other in list_note_paths(vault_path):
            if other == path:
                continue
            try:
                text = other.read_text(encoding="utf-8")
                if needle in text:
                    backlinks.append(other.stem)
            except Exception:
                continue
        result["backlinks"] = backlinks
    
    return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))])


async def handle_note_exists(vault_path: Path, args: Dict[str, Any]) -> CallToolResult:
    """🔍 Проверка существования заметки с рекомендациями"""
    title = args["title"]
    return_suggestions = args.get("return_suggestions", True)
    
    path = note_path_for_title(vault_path, title)
    exists = path.exists()
    
    result = {
        "tool": "note_exists",
        "title": title,
        "exists": exists
    }
    
    if exists:
        # Добавляем базовую информацию если существует
        try:
            stat = path.stat()
            result["basic_info"] = {
                "path": str(path.relative_to(vault_path)),
                "size_bytes": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
        except Exception as e:
            result["info_error"] = str(e)
    
    elif return_suggestions:
        # Предлагаем похожие заметки если не найдена
        similar_notes = []
        title_lower = title.lower()
        
        for note_path in list_note_paths(vault_path):
            note_title = note_path.stem.lower()
            # Простой поиск по подстроке
            if title_lower in note_title or note_title in title_lower:
                similar_notes.append(note_path.stem)
        
        result["suggestions"] = similar_notes[:5]  # Топ 5 похожих
    
    return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))])


async def handle_create_note_smart(vault_path: Path, args: Dict[str, Any]) -> CallToolResult:
    """✨ Умное создание заметки с автоматическими улучшениями"""
    title = args["title"]
    content = args["content"]
    tags = args.get("tags", [])
    folder = args.get("folder")
    auto_enhance = args.get("auto_enhance", True)
    suggest_connections = args.get("suggest_connections", True)
    
    # Проверяем существование
    path = note_path_for_title(vault_path, title, folder)
    if path.exists():
        return CallToolResult(content=[TextContent(type="text", text=f"❌ Note already exists: {title}")])
    
    result = {
        "tool": "create_note_smart",
        "title": title,
        "path": str(path)
    }
    
    # Автоматические улучшения
    if auto_enhance:
        # Автоматическое извлечение тегов из контента
        content_tags = re.findall(r'#(\w+)', content)
        suggested_tags = list(set(tags + content_tags))
        
        # Предложение папки на основе тегов и содержимого
        if not folder:
            # Простая логика предложения папок
            content_lower = content.lower()
            if any(word in content_lower for word in ['programming', 'code', 'python', 'javascript']):
                result["suggested_folder"] = "Programming"
            elif any(word in content_lower for word in ['project', 'task', 'work']):
                result["suggested_folder"] = "Projects"  
            elif any(word in content_lower for word in ['learn', 'study', 'course']):
                result["suggested_folder"] = "Learning"
        
        result["auto_tags"] = suggested_tags
        tags = suggested_tags  # Используем расширенный список тегов
    
    # Создание заметки
    metadata = {}
    if tags:
        metadata["tags"] = tags
    if auto_enhance:
        metadata["created_with"] = "enhanced_mcp_server"
        metadata["created_date"] = datetime.now().isoformat()
    
    write_note_frontmatter(path, content, metadata)
    result["created"] = True
    
    # Анализ возможных связей
    if suggest_connections:
        potential_connections = []
        content_words = set(content.lower().split())
        
        # Ищем существующие заметки с похожими словами
        for note_path in list_note_paths(vault_path):
            if note_path == path:
                continue
                
            note_title_words = set(note_path.stem.lower().split())
            # Простое пересечение слов
            common_words = content_words.intersection(note_title_words)
            if len(common_words) > 0:
                potential_connections.append({
                    "note": note_path.stem,
                    "reason": f"Common words: {', '.join(list(common_words)[:3])}"
                })
        
        result["suggested_connections"] = potential_connections[:5]
    
    return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))])


async def handle_append_to_note(vault_path: Path, args: Dict[str, Any]) -> CallToolResult:
    """📝 Умное добавление контента к заметке"""
    title = args["title"]
    content = args["content"]
    section = args.get("section")
    format_style = args.get("format_style", "append")
    add_timestamp = args.get("add_timestamp", False)
    
    path = note_path_for_title(vault_path, title)
    if not path.exists():
        return CallToolResult(content=[TextContent(type="text", text=f"❌ Note not found: {title}")])
    
    current_content, metadata = read_note_frontmatter(path)
    
    # Подготовка добавляемого контента
    addition = content
    
    if add_timestamp:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        addition = f"*{timestamp}*: {addition}"
    
    # Форматирование в зависимости от стиля
    if format_style == "bullet":
        addition = f"- {addition}"
    elif format_style == "heading":
        addition = f"## {addition}"
    elif format_style == "paragraph":
        addition = f"\n{addition}\n"
    
    # Добавление к конкретной секции или в конец
    if section:
        # Ищем секцию и добавляем в неё
        section_pattern = rf"(^#+\s+{re.escape(section)}.*?$)"
        if re.search(section_pattern, current_content, re.MULTILINE):
            # Секция найдена, добавляем после неё
            new_content = re.sub(
                section_pattern + r"(\n.*?)(?=^#+|\Z)",
                rf"\1\2\n{addition}",
                current_content,
                flags=re.MULTILINE | re.DOTALL
            )
        else:
            # Секция не найдена, создаем новую
            new_content = current_content.rstrip() + f"\n\n## {section}\n{addition}"
    else:
        # Простое добавление в конец
        separator = "\n\n" if not current_content.endswith("\n") else "\n"
        new_content = current_content + separator + addition
    
    write_note_frontmatter(path, new_content, metadata)
    
    result = {
        "tool": "append_to_note",
        "title": title,
        "appended": True,
        "format_used": format_style,
        "section_used": section if section else "end_of_note",
        "addition_preview": addition[:100] + "..." if len(addition) > 100 else addition
    }
    
    return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))])


async def handle_create_folder(vault_path: Path, args: Dict[str, Any]) -> CallToolResult:
    """📁 Создание структуры папок"""
    folder_path = args["folder_path"]
    create_index = args.get("create_index", True)
    index_template = args.get("index_template", "basic")
    
    full_path = vault_path / folder_path
    full_path.mkdir(parents=True, exist_ok=True)
    
    result = {
        "tool": "create_folder", 
        "folder_path": folder_path,
        "created": True,
        "full_path": str(full_path)
    }
    
    # Создание индексной заметки
    if create_index:
        index_name = f"{folder_path.split('/')[-1]} - Index"
        index_path = full_path / f"{index_name}.md"
        
        # Шаблоны для индексной заметки
        templates = {
            "basic": f"# {folder_path.split('/')[-1]}\n\n## Overview\n\nThis folder contains notes about {folder_path.split('/')[-1].lower()}.\n\n## Notes\n\n",
            "moc": f"# {folder_path.split('/')[-1]} - MOC (Map of Content)\n\n## Core Concepts\n\n## Related Notes\n\n## Resources\n\n",
            "structured": f"# {folder_path.split('/')[-1]}\n\n## 📋 Overview\n\n## 📝 Notes\n\n## 🔗 Related Topics\n\n## 📚 Resources\n\n## 🏷️ Tags\n\n"
        }
        
        index_content = templates.get(index_template, templates["basic"])
        index_path.write_text(index_content, encoding="utf-8")
        
        result["index_created"] = {
            "name": index_name,
            "template": index_template,
            "path": str(index_path.relative_to(vault_path))
        }
    
    return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))])


async def handle_explore_notes(vault_path: Path, args: Dict[str, Any]) -> CallToolResult:
    """🔍 Умный поиск заметок с индексацией и многоязычной поддержкой"""
    from .smart_search import SmartSearchEngine
    
    keywords = args["keywords"]
    search_in = args.get("search_in", "all")
    language_flexible = args.get("language_flexible", True)
    case_sensitive = args.get("case_sensitive", False) 
    limit = min(args.get("limit", 15), 30)  # Ограничение до 30
    include_content_preview = args.get("include_content_preview", True)
    min_relevance = args.get("min_relevance", 0.1)
    
    try:
        # Создаем поисковый движок
        search_engine = SmartSearchEngine(vault_path)
        
        # Выполняем поиск
        search_result = search_engine.search_notes(
            keywords=keywords,
            search_in=search_in,
            language_flexible=language_flexible,
            case_sensitive=case_sensitive,
            limit=limit,
            include_content_preview=include_content_preview,
            min_relevance=min_relevance
        )
        
        # Добавляем метаинформацию о поиске
        result = {
            "tool": "explore_notes",
            "timestamp": datetime.now().isoformat(),
            "search_performed": True,
            **search_result
        }
        
        return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))])
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in explore_notes: {e}")
        
        error_result = {
            "tool": "explore_notes",
            "error": str(e),
            "search_query": keywords,
            "results": [],
            "total_found": 0,
            "fallback_suggestion": "Try using list_notes or simplify your search keywords"
        }
        
        return CallToolResult(content=[TextContent(type="text", text=json.dumps(error_result, ensure_ascii=False, indent=2))])
