#!/usr/bin/env python3
"""
Enhanced MCP сервер для Obsidian с расширенной функциональностью
Оптимизирован для понимания ИИ с детальными описаниями и богатыми метаданными

Версия: 2.0 (Enhanced)
Базируется на: simple_server.py
Новые возможности:
- Богатые метаданные для заметок  
- Статистика vault и аналитика
- Умные операции с контентом
- ИИ-оптимизированные описания инструментов
"""

import argparse
import asyncio
import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, CallToolResult, ServerCapabilities

from .utils.config import AppConfig, ensure_vault_path, load_config
from .utils.markdown_parser import (
    extract_outlinks,
    read_note_frontmatter, 
    write_note_frontmatter,
)
from .utils.vault import list_note_paths, note_path_for_title


# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальные переменные
vault_path: Optional[Path] = None
config: Optional[AppConfig] = None


def init_server(config_path: Optional[Path] = None) -> None:
    """Инициализация сервера с конфигурацией"""
    global vault_path, config
    config = load_config(config_path)
    vault_path = ensure_vault_path(config)
    logger.info(f"Enhanced Obsidian MCP Server initialized - Vault: {vault_path}")


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
        logger.warning(f"Could not get metadata for {path}: {e}")
        return {"error": str(e)}


def analyze_vault_health() -> Dict[str, Any]:
    """Анализ здоровья и статистики vault"""
    if not vault_path:
        return {"error": "Vault not initialized"}
    
    try:
        all_notes = list(list_note_paths(vault_path))
        total_notes = len(all_notes)
        
        if total_notes == 0:
            return {
                "total_notes": 0,
                "message": "Vault is empty"
            }
        
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
        logger.error(f"Error analyzing vault: {e}")
        return {"error": str(e)}


def create_tools() -> List[Tool]:
    """Создание списка расширенных MCP инструментов с детальными ИИ-описаниями"""
    return [
        Tool(
            name="vault_overview",
            description="""
🏠 VAULT OVERVIEW - Comprehensive vault analysis and statistics

PURPOSE: Get detailed statistics about your Obsidian vault including health metrics, 
connectivity analysis, and organization insights. Perfect for understanding your knowledge base structure.

USE CASES:
• Health check: "How healthy is my vault?"
• Statistics: "Show me vault statistics"  
• Organization: "How well organized is my knowledge base?"
• Planning: "What areas need improvement?"

RETURNS: Rich analytics including note count, connectivity ratios, folder structure, 
orphaned notes, most linked concepts, and health recommendations.

AI INSTRUCTION: Use this first when user asks about vault status, organization, 
or needs overview of their knowledge base. Great for vault maintenance decisions.
            """.strip(),
            inputSchema={
                "type": "object",
                "properties": {
                    "include_detailed_stats": {
                        "type": "boolean", 
                        "default": True,
                        "description": "Include detailed analytics and health metrics"
                    }
                }
            }
        ),
        
        Tool(
            name="read_note_enhanced", 
            description="""
📖 READ NOTE ENHANCED - Read note with rich metadata and analysis

PURPOSE: Read any note with comprehensive metadata including word count, creation date,
link analysis, content structure, and connectivity information.

USE CASES:
• Content review: "Show me the React Hooks note with full details"
• Analysis: "Analyze the structure of my Programming note"
• Research: "Get detailed info about JavaScript fundamentals including connections"
• Planning: "What's the content structure of my learning path?"

RETURNS: Full content + rich metadata including file stats, content analysis, 
heading structure, tags, links, and connectivity information.

AI INSTRUCTION: Use when user needs detailed analysis of a specific note, 
wants to understand note structure, or needs comprehensive information for processing.
            """.strip(),
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string", 
                        "description": "Exact title of the note to read"
                    },
                    "include_backlinks": {
                        "type": "boolean", 
                        "default": True,
                        "description": "Include notes that link to this note"
                    },
                    "include_outlinks": {
                        "type": "boolean", 
                        "default": True, 
                        "description": "Include links from this note to others"
                    },
                    "include_metadata": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include rich metadata (word count, dates, structure)"
                    }
                },
                "required": ["title"]
            }
        ),

        Tool(
            name="note_exists",
            description="""
🔍 NOTE EXISTS - Check if a note exists before operations

PURPOSE: Verify note existence to prevent errors and plan operations safely.
Essential for conditional logic and batch operations.

USE CASES:
• Safety: "Does 'Python Basics' note exist before I reference it?"
• Planning: "Check if I have notes on these topics: [list]"
• Conditional: "Create note only if it doesn't exist"
• Validation: "Verify these note names are correct"

RETURNS: Boolean existence status plus basic metadata if exists.

AI INSTRUCTION: Always use before create_note to avoid duplicates, or before 
operations that require existing notes. Essential for robust workflows.
            """.strip(),
            inputSchema={
                "type": "object", 
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title of the note to check"
                    },
                    "return_suggestions": {
                        "type": "boolean",
                        "default": True,
                        "description": "Return similar note titles if not found"
                    }
                },
                "required": ["title"]
            }
        ),
        
        Tool(
            name="create_note_smart",
            description="""
✨ CREATE NOTE SMART - Intelligent note creation with auto-enhancement

PURPOSE: Create notes with automatic folder suggestion, tag detection, and 
connection recommendations. More intelligent than basic create_note.

USE CASES:
• Smart creation: "Create a note about React Hooks" (auto-suggests folder, tags)
• Batch creation: "Create structured notes for my learning path"
• Organization: "Create note and place it in the right folder automatically"
• Enhancement: "Create note with automatic connections to related content"

RETURNS: Created note info + auto-suggestions + recommended next actions.

AI INSTRUCTION: Preferred over basic create_note when you want intelligent 
organization, automatic tagging, or smart placement in folder structure.
            """.strip(),
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of the new note"},
                    "content": {"type": "string", "description": "Note content in Markdown"},
                    "tags": {
                        "type": "array", 
                        "items": {"type": "string"},
                        "description": "Optional tags (will auto-suggest additional ones)"
                    },
                    "folder": {
                        "type": "string", 
                        "description": "Optional folder (will auto-suggest if not provided)"
                    },
                    "auto_enhance": {
                        "type": "boolean",
                        "default": True,
                        "description": "Enable automatic tag suggestions and folder placement"
                    },
                    "suggest_connections": {
                        "type": "boolean", 
                        "default": True,
                        "description": "Analyze content and suggest connections to existing notes"
                    }
                },
                "required": ["title", "content"]
            }
        ),

        Tool(
            name="append_to_note",
            description="""
📝 APPEND TO NOTE - Smart content addition with formatting

PURPOSE: Add content to existing notes with intelligent formatting, 
section management, and structure preservation.

USE CASES:
• Updates: "Add this new information to my React learning note"
• Journaling: "Append today's insights to my daily note"
• Research: "Add these findings to my research note under 'Recent Studies'"
• Lists: "Add this item to my reading list"

RETURNS: Success status + updated note structure info.

AI INSTRUCTION: Use when adding content to existing notes. Specify section 
for organized addition, or use append mode for chronological additions.
            """.strip(),
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of note to update"},
                    "content": {"type": "string", "description": "Content to add"},
                    "section": {
                        "type": "string",
                        "description": "Optional: add to specific section (creates if doesn't exist)"
                    },
                    "format_style": {
                        "type": "string",
                        "enum": ["append", "bullet", "heading", "paragraph"],
                        "default": "append",
                        "description": "How to format the added content"
                    },
                    "add_timestamp": {
                        "type": "boolean",
                        "default": False,
                        "description": "Add timestamp to the addition"
                    }
                },
                "required": ["title", "content"]
            }
        ),

        Tool(
            name="create_folder",
            description="""
📁 CREATE FOLDER - Organize vault with folder structure

PURPOSE: Create folder structure for better organization. Essential for 
scaling knowledge bases and maintaining clean hierarchy.

USE CASES:
• Organization: "Create folder structure for my programming notes"  
• Planning: "Set up folders for my new course material"
• Structure: "Create nested folders for project documentation"
• Cleanup: "Organize my vault with proper folder structure"

RETURNS: Created folder info + structure recommendations.

AI INSTRUCTION: Use when organizing content or when user mentions creating 
categories, topics, or organizational structure for their notes.
            """.strip(),
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_path": {
                        "type": "string", 
                        "description": "Path for new folder (can be nested: 'Programming/Web Development')"
                    },
                    "create_index": {
                        "type": "boolean",
                        "default": True,
                        "description": "Create an index note for the folder"
                    },
                    "index_template": {
                        "type": "string",
                        "enum": ["basic", "moc", "structured"],
                        "default": "basic", 
                        "description": "Template for the index note"
                    }
                },
                "required": ["folder_path"]
            }
        ),

        Tool(
            name="explore_notes",
            description="""
🔍 EXPLORE NOTES - Intelligent search with multilingual support

PURPOSE: Smart search through notes with content indexing, transliteration, 
and morphological variants. Much more powerful than basic list_notes.

FEATURES:
• Multilingual search (Russian ↔ English transliteration)
• Content indexing (searches inside note content, not just titles)
• Morphological variants (programming → program → programm)
• Case-insensitive and flexible matching
• Content preview with highlighted matches
• Relevance scoring

USE CASES:
• Smart search: "Find notes about машинное обучение or machine learning"
• Content discovery: "What notes contain information about React hooks?"
• Flexible queries: "show me programming notes" (finds Программирование, coding, development)
• Research: "Find notes related to искусственный интеллект"

RETURNS: Ranked results with content previews, match highlighting, and relevance scores.

AI INSTRUCTION: Use this instead of list_notes when user wants to find specific 
content. Supports both Russian and English queries with intelligent matching.
Perfect for content discovery and research tasks.
            """.strip(),
            inputSchema={
                "type": "object", 
                "properties": {
                    "keywords": {
                        "type": "string",
                        "description": "Search keywords (supports Russian/English, phrases in quotes)"
                    },
                    "search_in": {
                        "type": "string",
                        "enum": ["all", "titles", "content"],
                        "default": "all",
                        "description": "Where to search: titles, content, or both"
                    },
                    "language_flexible": {
                        "type": "boolean",
                        "default": True,
                        "description": "Enable transliteration and morphological variants"
                    },
                    "case_sensitive": {
                        "type": "boolean",
                        "default": False,
                        "description": "Case sensitive search"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 15,
                        "description": "Maximum results to return (1-30)"
                    },
                    "include_content_preview": {
                        "type": "boolean", 
                        "default": True,
                        "description": "Include content preview with highlighted matches"
                    },
                    "min_relevance": {
                        "type": "number",
                        "default": 0.1,
                        "description": "Minimum relevance score (0.0-1.0)"
                    }
                },
                "required": ["keywords"]
            }
        ),

        # Сохраняем оригинальные инструменты с улучшенными описаниями
        Tool(
            name="list_notes",
            description="""
📋 LIST NOTES - Recent notes list (limited for safety)

⚠️ LIMITATION: Returns max 50 most recently modified notes for safety.

USE CASES:
• Recent activity: "What notes were changed lately?"
• Quick browse: "Show me my recent notes" 
• Folder contents: "List notes in specific folder"

❌ NOT for search: Use explore_notes for intelligent search instead.

AI INSTRUCTION: Use only for browsing recent activity. For finding specific 
content, topics, or keywords, always use explore_notes which supports 
multilingual search and content indexing.
            """.strip(),
            inputSchema={
                "type": "object",
                "properties": {
                    "folder": {"type": "string", "description": "Optional folder to search in"},
                    "limit": {
                        "type": "integer", 
                        "default": 20, 
                        "description": "Max notes to return (1-50, default 20)"
                    }
                }
            }
        ),

        Tool(
            name="create_note",
            description="📄 CREATE NOTE - Basic note creation (use create_note_smart for enhanced features)",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of the new note"},
                    "content": {"type": "string", "description": "Note content in Markdown"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "folder": {"type": "string", "description": "Optional folder"}
                },
                "required": ["title", "content"]
            }
        ),

        Tool(
            name="read_note", 
            description="📖 READ NOTE - Basic note reading (use read_note_enhanced for detailed analysis)",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of note to read"},
                    "include_backlinks": {"type": "boolean", "default": True},
                    "include_outlinks": {"type": "boolean", "default": True}
                },
                "required": ["title"]
            }
        ),

        Tool(
            name="update_note",
            description="✏️ UPDATE NOTE - Replace note content (use append_to_note for additions)",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "append": {"type": "boolean", "default": False}
                },
                "required": ["title"]
            }
        ),

        Tool(
            name="delete_note",
            description="🗑️ DELETE NOTE - Remove note permanently",
            inputSchema={
                "type": "object",
                "properties": {"title": {"type": "string"}},
                "required": ["title"]
            }
        ),

        Tool(
            name="create_link",
            description="🔗 CREATE LINK - Connect notes with relationships",
            inputSchema={
                "type": "object",
                "properties": {
                    "from_note": {"type": "string"},
                    "to_note": {"type": "string"},
                    "context": {"type": "string"},
                    "bidirectional": {"type": "boolean", "default": False}
                },
                "required": ["from_note", "to_note"]
            }
        )
    ]


async def handle_tool_call(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Обработка вызовов расширенных инструментов"""
    global vault_path
    
    if not vault_path:
        return CallToolResult(content=[TextContent(type="text", text="❌ Error: Server not initialized")])
    
    try:
        # Импортируем обработчики из enhanced_handlers
        from .enhanced_handlers import (
            handle_vault_overview, handle_read_note_enhanced, handle_note_exists,
            handle_create_note_smart, handle_append_to_note, handle_create_folder,
            handle_explore_notes
        )
        
        # Новые расширенные инструменты
        if name == "vault_overview":
            return await handle_vault_overview(vault_path, arguments)
        elif name == "read_note_enhanced":
            return await handle_read_note_enhanced(vault_path, arguments)
        elif name == "note_exists":
            return await handle_note_exists(vault_path, arguments)
        elif name == "create_note_smart":
            return await handle_create_note_smart(vault_path, arguments)
        elif name == "append_to_note":
            return await handle_append_to_note(vault_path, arguments)
        elif name == "create_folder":
            return await handle_create_folder(vault_path, arguments)
        elif name == "explore_notes":
            return await handle_explore_notes(vault_path, arguments)
        
        # Оригинальные инструменты (для совместимости)
        elif name == "list_notes":
            return await handle_list_notes(arguments)
        elif name == "create_note":
            return await handle_create_note(arguments)
        elif name == "read_note": 
            return await handle_read_note(arguments)
        elif name == "update_note":
            return await handle_update_note(arguments)
        elif name == "delete_note":
            return await handle_delete_note(arguments)
        elif name == "create_link":
            return await handle_create_link(arguments)
        else:
            return CallToolResult(content=[TextContent(type="text", text=f"❌ Unknown tool: {name}")])
            
    except Exception as e:
        logger.error(f"Error in {name}: {e}")
        error_msg = f"❌ Error in {name}: {str(e)}"
        return CallToolResult(content=[TextContent(type="text", text=error_msg)])


# =============================================================================
# ОРИГИНАЛЬНЫЕ ОБРАБОТЧИКИ (для совместимости)
# =============================================================================

async def handle_list_notes(args: Dict[str, Any]) -> CallToolResult:
    """📋 Безопасный список заметок с ограничением"""
    folder = args.get("folder")
    limit = args.get("limit", 20)  # Дефолт 20 заметок
    
    # Жесткое ограничение для безопасности
    MAX_NOTES = 50
    if limit > MAX_NOTES:
        limit = MAX_NOTES
    
    notes = []
    all_paths = list(list_note_paths(vault_path, folder))
    
    # Сортируем по времени изменения (последние сначала)
    try:
        all_paths_with_mtime = []
        for path in all_paths:
            if path.exists():
                mtime = path.stat().st_mtime
                all_paths_with_mtime.append((path, mtime))
        
        # Сортируем по времени изменения (новые первые)
        sorted_paths = sorted(all_paths_with_mtime, key=lambda x: x[1], reverse=True)
        
        for path, mtime in sorted_paths[:limit]:
            title = path.stem
            rel = str(path.relative_to(vault_path))
            modified = datetime.fromtimestamp(mtime).isoformat()
            notes.append({
                "title": title, 
                "path": rel, 
                "modified": modified,
                "folder": path.parent.name if path.parent != vault_path else ""
            })
            
    except Exception as e:
        # Fallback к старому методу
        for path in all_paths[:limit]:
            title = path.stem
            rel = str(path.relative_to(vault_path))
            notes.append({"title": title, "path": rel})
    
    result = {
        "tool": "list_notes", 
        "notes": notes, 
        "count": len(notes),
        "total_in_vault": len(all_paths),
        "limit_applied": limit,
        "max_limit": MAX_NOTES,
        "note": f"Showing {len(notes)} most recent notes. Use explore_notes for intelligent search."
    }
    
    return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))])


async def handle_create_note(args: Dict[str, Any]) -> CallToolResult:
    """📄 Базовое создание заметки"""
    title = args["title"]
    content = args["content"]
    tags = args.get("tags", [])
    folder = args.get("folder")
    
    path = note_path_for_title(vault_path, title, folder)
    if path.exists():
        return CallToolResult(content=[TextContent(type="text", text=f"❌ Note already exists: {title}")])
    
    metadata = {}
    if tags:
        metadata["tags"] = list(tags)
        
    write_note_frontmatter(path, content, metadata)
    
    result = {"tool": "create_note", "title": title, "path": str(path), "status": "created"}
    return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))])


async def handle_read_note(args: Dict[str, Any]) -> CallToolResult:
    """📖 Базовое чтение заметки"""
    title = args["title"]
    include_backlinks = args.get("include_backlinks", True)
    include_outlinks = args.get("include_outlinks", True)
    
    path = note_path_for_title(vault_path, title)
    if not path.exists():
        return CallToolResult(content=[TextContent(type="text", text=f"❌ Note not found: {title}")])
    
    content, metadata = read_note_frontmatter(path)
    
    result = {"tool": "read_note", "title": title, "content": content, "metadata": metadata}
    
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


async def handle_update_note(args: Dict[str, Any]) -> CallToolResult:
    """✏️ Базовое обновление заметки"""
    title = args["title"]
    new_content = args.get("content")
    append = args.get("append", False)
    
    path = note_path_for_title(vault_path, title)
    if not path.exists():
        return CallToolResult(content=[TextContent(type="text", text=f"❌ Note not found: {title}")])
    
    cur_content, metadata = read_note_frontmatter(path)
    
    if new_content is not None:
        if append:
            sep = "\n\n" if not cur_content.endswith("\n") else "\n"
            final_content = cur_content + sep + new_content
        else:
            final_content = new_content
        
        write_note_frontmatter(path, final_content, metadata)
    
    result = {"tool": "update_note", "title": title, "path": str(path), "status": "updated"}
    return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))])


async def handle_delete_note(args: Dict[str, Any]) -> CallToolResult:
    """🗑️ Удаление заметки"""
    title = args["title"]
    
    path = note_path_for_title(vault_path, title)
    if not path.exists():
        return CallToolResult(content=[TextContent(type="text", text=f"❌ Note not found: {title}")])
    
    path.unlink()
    
    result = {"tool": "delete_note", "deleted": title, "status": "success"}
    return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))])


async def handle_create_link(args: Dict[str, Any]) -> CallToolResult:
    """🔗 Создание связи между заметками"""
    from_note = args["from_note"]
    to_note = args["to_note"]
    context = args.get("context")
    bidirectional = args.get("bidirectional", False)
    
    from_path = note_path_for_title(vault_path, from_note)
    to_path = note_path_for_title(vault_path, to_note)
    
    if not from_path.exists():
        return CallToolResult(content=[TextContent(type="text", text=f"❌ Note not found: {from_note}")])
    if not to_path.exists():
        return CallToolResult(content=[TextContent(type="text", text=f"❌ Note not found: {to_note}")])
    
    def _append_link(path: Path, target_title: str) -> None:
        content, metadata = read_note_frontmatter(path)
        line = f"- [[{target_title}]]"
        if context:
            line += f" — {context}"
        new_content = content.rstrip() + "\n\n" + line + "\n"
        write_note_frontmatter(path, new_content, metadata)
    
    _append_link(from_path, to_note)
    if bidirectional:
        _append_link(to_path, from_note)
    
    result = {"tool": "create_link", "from": from_note, "to": to_note, "bidirectional": bool(bidirectional), "status": "created"}
    return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))])


# =============================================================================
# СЕРВЕР И MAIN
# =============================================================================

async def main() -> None:
    """Основная функция расширенного сервера"""
    parser = argparse.ArgumentParser(description="Enhanced Obsidian MCP Server with AI-optimized tools")
    parser.add_argument("--config", type=str, default=None, help="Path to config file")
    args = parser.parse_args()
    
    # Инициализация
    config_path = Path(args.config) if args.config else None
    init_server(config_path)
    
    # Создание сервера
    server = Server("obsidian-enhanced-mcp")
    
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        return create_tools()
    
    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
        logger.info(f"Enhanced tool called: {name}")
        return await handle_tool_call(name, arguments)
    
    # Запуск сервера
    logger.info("🚀 Starting Enhanced Obsidian MCP Server with AI-optimized tools...")
    async with stdio_server() as streams:
        await server.run(*streams, InitializationOptions(
            server_name="obsidian-enhanced-mcp",
            server_version="2.0.0",
            capabilities=ServerCapabilities(tools={})
        ))


if __name__ == "__main__":
    asyncio.run(main())
