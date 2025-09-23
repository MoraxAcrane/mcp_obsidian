from __future__ import annotations

import argparse
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession

from .utils.config import AppConfig, ensure_vault_path, load_config
from .utils.markdown_parser import (
    extract_outlinks,
    read_note_frontmatter,
    replace_section,
    write_note_frontmatter,
)
from .utils.vault import list_note_paths, note_path_for_title


@dataclass
class AppContext:
    vault_path: Path
    config: AppConfig


def create_server(config_path: Optional[Path] = None) -> FastMCP:
    @asynccontextmanager
    async def lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
        config = load_config(config_path)
        vault_path = ensure_vault_path(config)
        ctx = AppContext(vault_path=vault_path, config=config)
        try:
            yield ctx
        finally:
            pass

    mcp = FastMCP("obsidian-ai-mcp", lifespan=lifespan)

    @mcp.tool()
    def list_notes(
        ctx: Context[ServerSession, AppContext], 
        folder: Optional[str] = None, 
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        📋 LIST NOTES - Recent notes list (limited for safety)
        
        ⚠️ LIMITATION: Returns max 50 most recently modified notes for safety.
        
        USE CASES:
        • Recent activity: "What notes were changed lately?"
        • Quick browse: "Show me my recent notes" 
        • Folder contents: "List notes in specific folder"
        
        ❌ NOT for search: Use explore_notes for intelligent search instead.
        """
        vault_path = ctx.request_context.lifespan_context.vault_path
        
        # Жесткое ограничение для безопасности
        MAX_NOTES = 50
        if limit is None:
            limit = 20  # Дефолт
        if limit > MAX_NOTES:
            limit = MAX_NOTES
        
        notes = []
        all_paths = list(list_note_paths(vault_path, folder))
        
        # Сортируем по времени изменения (последние сначала)
        try:
            from datetime import datetime
            
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
        
        return {
            "notes": notes, 
            "count": len(notes),
            "total_in_vault": len(all_paths),
            "limit_applied": limit,
            "max_limit": MAX_NOTES,
            "note": f"Showing {len(notes)} most recent notes. Use explore_notes for intelligent search."
        }

    @mcp.tool()
    def create_note(
        ctx: Context[ServerSession, AppContext],
        title: str,
        content: str,
        tags: Optional[List[str]] = None,
        folder: Optional[str] = None,
        template: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new note with optional tags and folder."""
        vault_path = ctx.request_context.lifespan_context.vault_path
        path = note_path_for_title(vault_path, title, folder)
        if path.exists():
            raise ValueError(f"Note already exists: {title}")
        metadata: Dict[str, Any] = {}
        if tags:
            metadata["tags"] = list(tags)
        # Template support is a future enhancement
        write_note_frontmatter(path, content, metadata)
        return {"title": title, "path": str(path)}

    @mcp.tool()
    def read_note(
        ctx: Context[ServerSession, AppContext],
        title: str,
        include_backlinks: bool = True,
        include_outlinks: bool = True,
    ) -> Dict[str, Any]:
        """Read a note's content and metadata."""
        vault_path = ctx.request_context.lifespan_context.vault_path
        path = note_path_for_title(vault_path, title)
        if not path.exists():
            raise FileNotFoundError(f"Note not found: {title}")
        content, metadata = read_note_frontmatter(path)
        result: Dict[str, Any] = {"title": title, "content": content, "metadata": metadata}
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
                except Exception:
                    continue
                if needle in text:
                    backlinks.append(other.stem)
            result["backlinks"] = backlinks
        return result

    @mcp.tool()
    def update_note(
        ctx: Context[ServerSession, AppContext],
        title: str,
        content: Optional[str] = None,
        append: bool = False,
        section: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update a note: replace, append, or update a specific section."""
        vault_path = ctx.request_context.lifespan_context.vault_path
        path = note_path_for_title(vault_path, title)
        if not path.exists():
            raise FileNotFoundError(f"Note not found: {title}")
        cur_content, metadata = read_note_frontmatter(path)
        new_content = cur_content
        if content is not None:
            if section:
                new_content = replace_section(cur_content, section, content)
            elif append:
                sep = "\n\n" if not cur_content.endswith("\n") else "\n"
                new_content = cur_content + sep + content
            else:
                new_content = content
        write_note_frontmatter(path, new_content, metadata)
        return {"title": title, "path": str(path)}

    @mcp.tool()
    def delete_note(ctx: Context[ServerSession, AppContext], title: str) -> Dict[str, Any]:
        """Delete a note by title."""
        vault_path = ctx.request_context.lifespan_context.vault_path
        path = note_path_for_title(vault_path, title)
        if not path.exists():
            raise FileNotFoundError(f"Note not found: {title}")
        path.unlink()
        return {"deleted": title}

    @mcp.tool()
    def create_link(
        ctx: Context[ServerSession, AppContext],
        from_note: str,
        to_note: str,
        link_type: str = "direct",
        context: Optional[str] = None,
        bidirectional: bool = False,
    ) -> Dict[str, Any]:
        """Create a link between notes by inserting [[to_note]] in from_note (and optionally back)."""
        vault_path = ctx.request_context.lifespan_context.vault_path
        from_path = note_path_for_title(vault_path, from_note)
        to_path = note_path_for_title(vault_path, to_note)
        if not from_path.exists():
            raise FileNotFoundError(f"Note not found: {from_note}")
        if not to_path.exists():
            raise FileNotFoundError(f"Note not found: {to_note}")

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
        return {"from": from_note, "to": to_note, "bidirectional": bool(bidirectional), "type": link_type}

    @mcp.tool()
    def explore_notes(
        ctx: Context[ServerSession, AppContext],
        keywords: str,
        search_in: str = "all",  # "all", "titles", "content"
        language_flexible: bool = True,
        case_sensitive: bool = False,
        limit: int = 15,
        include_content_preview: bool = True,
        min_relevance: float = 0.1
    ) -> Dict[str, Any]:
        """
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
        """
        try:
            from .smart_search import SmartSearchEngine
            
            vault_path = ctx.request_context.lifespan_context.vault_path
            
            # Ограничиваем количество результатов
            limit = min(limit, 30)
            
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
            from datetime import datetime
            result = {
                "tool": "explore_notes",
                "timestamp": datetime.now().isoformat(),
                "search_performed": True,
                **search_result
            }
            
            return result
            
        except Exception as e:
            # Возвращаем ошибку в структурированном виде
            return {
                "tool": "explore_notes",
                "error": str(e),
                "search_query": keywords,
                "results": [],
                "total_found": 0,
                "fallback_suggestion": "Try using list_notes or simplify your search keywords"
            }

    return mcp


def main() -> None:
    parser = argparse.ArgumentParser(description="Obsidian AI MCP Server")
    parser.add_argument("--config", type=str, default=None, help="Path to obsidian_mcp_config.yaml")
    parser.add_argument(
        "--transport",
        type=str,
        default="stdio",
        choices=["stdio", "sse", "streamable-http"],
        help="Transport type (default: stdio)",
    )
    parser.add_argument("--port", type=int, default=8000, help="Port for SSE/HTTP transports")
    args = parser.parse_args()

    cfg_path = Path(args.config) if args.config else None
    server = create_server(cfg_path)

    if args.transport == "stdio":
        server.run()
    elif args.transport == "sse":
        server.run(transport="sse", port=args.port)
    else:
        server.run(transport="streamable-http", port=args.port)


if __name__ == "__main__":
    main()


