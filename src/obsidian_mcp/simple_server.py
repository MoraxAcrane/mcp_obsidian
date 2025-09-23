#!/usr/bin/env python3
"""
Упрощенный MCP сервер для Obsidian без тяжелых зависимостей
Использует только базовый MCP протокол без FastMCP
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import ServerCapabilities
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, CallToolResult

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
    logger.info(f"Vault path: {vault_path}")


def create_tools() -> List[Tool]:
    """Создание списка доступных инструментов MCP"""
    return [
        Tool(
            name="list_notes",
            description="List notes in the vault (optionally within a folder)",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder": {"type": "string", "description": "Optional folder to search in"},
                    "limit": {"type": "integer", "description": "Maximum number of notes to return"}
                }
            }
        ),
        Tool(
            name="create_note", 
            description="Create a new note with optional tags and folder",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of the note"},
                    "content": {"type": "string", "description": "Content of the note"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Optional tags"},
                    "folder": {"type": "string", "description": "Optional folder to place note in"}
                },
                "required": ["title", "content"]
            }
        ),
        Tool(
            name="read_note",
            description="Read a note's content and metadata",
            inputSchema={
                "type": "object", 
                "properties": {
                    "title": {"type": "string", "description": "Title of the note to read"},
                    "include_backlinks": {"type": "boolean", "default": True},
                    "include_outlinks": {"type": "boolean", "default": True}
                },
                "required": ["title"]
            }
        ),
        Tool(
            name="update_note",
            description="Update an existing note",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of the note to update"},
                    "content": {"type": "string", "description": "New content"},
                    "append": {"type": "boolean", "default": False, "description": "Append to existing content"}
                },
                "required": ["title"]
            }
        ),
        Tool(
            name="delete_note",
            description="Delete a note by title",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of the note to delete"}
                },
                "required": ["title"]
            }
        ),
        Tool(
            name="create_link",
            description="Create a link between notes",
            inputSchema={
                "type": "object",
                "properties": {
                    "from_note": {"type": "string", "description": "Source note title"},
                    "to_note": {"type": "string", "description": "Target note title"}, 
                    "context": {"type": "string", "description": "Optional context for the link"},
                    "bidirectional": {"type": "boolean", "default": False}
                },
                "required": ["from_note", "to_note"]
            }
        )
    ]


async def handle_tool_call(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Обработка вызовов инструментов"""
    global vault_path
    
    if not vault_path:
        return CallToolResult(content=[TextContent(type="text", text="Error: Server not initialized")])
    
    try:
        if name == "list_notes":
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
            return CallToolResult(content=[TextContent(type="text", text=f"Unknown tool: {name}")])
            
    except Exception as e:
        logger.error(f"Error in {name}: {e}")
        return CallToolResult(content=[TextContent(type="text", text=f"Error: {str(e)}")])


async def handle_list_notes(args: Dict[str, Any]) -> CallToolResult:
    """Список заметок"""
    folder = args.get("folder")
    limit = args.get("limit")
    
    notes = []
    for path in list_note_paths(vault_path, folder):
        title = path.stem
        rel = str(path.relative_to(vault_path))
        notes.append({"title": title, "path": rel})
        if limit and len(notes) >= limit:
            break
    
    result = json.dumps(notes, ensure_ascii=False, indent=2)
    return CallToolResult(content=[TextContent(type="text", text=result)])


async def handle_create_note(args: Dict[str, Any]) -> CallToolResult:
    """Создание заметки"""
    title = args["title"]
    content = args["content"]
    tags = args.get("tags", [])
    folder = args.get("folder")
    
    path = note_path_for_title(vault_path, title, folder)
    if path.exists():
        return CallToolResult(content=[TextContent(type="text", text=f"Error: Note already exists: {title}")])
    
    metadata: Dict[str, Any] = {}
    if tags:
        metadata["tags"] = list(tags)
        
    write_note_frontmatter(path, content, metadata)
    
    result = {"title": title, "path": str(path), "status": "created"}
    return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))])


async def handle_read_note(args: Dict[str, Any]) -> CallToolResult:
    """Чтение заметки"""
    title = args["title"]
    include_backlinks = args.get("include_backlinks", True)
    include_outlinks = args.get("include_outlinks", True)
    
    path = note_path_for_title(vault_path, title)
    if not path.exists():
        return CallToolResult(content=[TextContent(type="text", text=f"Error: Note not found: {title}")])
    
    content, metadata = read_note_frontmatter(path)
    
    result: Dict[str, Any] = {
        "title": title,
        "content": content,
        "metadata": metadata
    }
    
    if include_outlinks:
        result["outlinks"] = extract_outlinks(content)
        
    if include_backlinks:
        backlinks: List[str] = []
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
    """Обновление заметки"""
    title = args["title"]
    new_content = args.get("content")
    append = args.get("append", False)
    
    path = note_path_for_title(vault_path, title)
    if not path.exists():
        return CallToolResult(content=[TextContent(type="text", text=f"Error: Note not found: {title}")])
    
    cur_content, metadata = read_note_frontmatter(path)
    
    if new_content is not None:
        if append:
            sep = "\n\n" if not cur_content.endswith("\n") else "\n"
            final_content = cur_content + sep + new_content
        else:
            final_content = new_content
        
        write_note_frontmatter(path, final_content, metadata)
    
    result = {"title": title, "path": str(path), "status": "updated"}
    return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))])


async def handle_delete_note(args: Dict[str, Any]) -> CallToolResult:
    """Удаление заметки"""
    title = args["title"]
    
    path = note_path_for_title(vault_path, title)
    if not path.exists():
        return CallToolResult(content=[TextContent(type="text", text=f"Error: Note not found: {title}")])
    
    path.unlink()
    
    result = {"deleted": title, "status": "success"}
    return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))])


async def handle_create_link(args: Dict[str, Any]) -> CallToolResult:
    """Создание связи между заметками"""
    from_note = args["from_note"]
    to_note = args["to_note"]
    context = args.get("context")
    bidirectional = args.get("bidirectional", False)
    
    from_path = note_path_for_title(vault_path, from_note)
    to_path = note_path_for_title(vault_path, to_note)
    
    if not from_path.exists():
        return CallToolResult(content=[TextContent(type="text", text=f"Error: Note not found: {from_note}")])
    if not to_path.exists():
        return CallToolResult(content=[TextContent(type="text", text=f"Error: Note not found: {to_note}")])
    
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
    
    result = {"from": from_note, "to": to_note, "bidirectional": bool(bidirectional), "status": "created"}
    return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))])


async def main() -> None:
    """Основная функция сервера"""
    parser = argparse.ArgumentParser(description="Simple Obsidian MCP Server")
    parser.add_argument("--config", type=str, default=None, help="Path to config file")
    args = parser.parse_args()
    
    # Инициализация
    config_path = Path(args.config) if args.config else None
    init_server(config_path)
    
    # Создание сервера
    server = Server("obsidian-simple-mcp")
    
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        return create_tools()
    
    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
        logger.info(f"Tool called: {name}")
        return await handle_tool_call(name, arguments)
    
    # Запуск сервера
    logger.info("Starting Simple Obsidian MCP Server...")
    async with stdio_server() as streams:
        await server.run(*streams, InitializationOptions(
            server_name="obsidian-simple-mcp",
            server_version="0.1.0",
            capabilities=ServerCapabilities(
                tools={}
            )
        ))


if __name__ == "__main__":
    asyncio.run(main())
