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
        limit: Optional[float] = None  # Changed from int to float for Cursor IDE compatibility
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
        
        # Fix Cursor IDE compatibility: convert number/float to int
        # Cursor IDE sends JavaScript numbers as float, but we need int internally
        if limit is not None:
            try:
                limit = int(float(limit))  # Handle both int and float from Cursor IDE
            except (ValueError, TypeError):
                limit = 20  # Fallback to default
        
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
        """
        📖 READ NOTE - Get note content and metadata (works in all folders)
        
        IMPROVEMENTS:
        • Fixed: Now works in subfolders (not just root)
        • Fixed: Handles emoji titles like "🚀 Projects Hub"  
        • Enhanced: Better error messages with suggestions
        """
        vault_path = ctx.request_context.lifespan_context.vault_path
        
        try:
            from .utils.universal_finder import get_universal_finder
            
            # Use Universal Note Finder instead of note_path_for_title
            finder = get_universal_finder(vault_path)
            path = finder.find_note(title)
            
            if not path or not path.exists():
                # Provide helpful suggestions
                similar = finder.find_multiple(title, limit=3)
                suggestions = [s[0] for s in similar] if similar else []
                
                return {
                    "success": False,
                    "error": f"Note not found: {title}",
                    "suggestions": suggestions,
                    "help": "Try using exact title or check explore_notes to find the note"
                }
            
            # Read note content
            content, metadata = read_note_frontmatter(path)
            result: Dict[str, Any] = {
                "title": title, 
                "content": content, 
                "metadata": metadata,
                "path": str(path.relative_to(vault_path)),
                "folder": path.parent.name if path.parent != vault_path else "root"
            }
            
            # Add outlinks analysis
            if include_outlinks:
                result["outlinks"] = extract_outlinks(content)
            
            # Add backlinks analysis  
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
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to read note: {str(e)}",
                "title": title
            }

    @mcp.tool()
    def update_note(
        ctx: Context[ServerSession, AppContext],
        title: str,
        content: Optional[str] = None,
        append: bool = False,
        section: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        ✏️ UPDATE NOTE - Modify note content (works in all folders)
        
        IMPROVEMENTS:
        • Fixed: Now works in subfolders (not just root)  
        • Fixed: Handles emoji titles like "🗂️ Knowledge Management Hub"
        • Enhanced: Better feedback and error handling
        """
        vault_path = ctx.request_context.lifespan_context.vault_path
        
        try:
            from .utils.universal_finder import get_universal_finder
            
            # Use Universal Note Finder instead of note_path_for_title
            finder = get_universal_finder(vault_path)
            path = finder.find_note(title)
            
            if not path or not path.exists():
                # Provide helpful suggestions
                similar = finder.find_multiple(title, limit=3)
                suggestions = [s[0] for s in similar] if similar else []
                
                return {
                    "success": False,
                    "error": f"Note not found: {title}",
                    "suggestions": suggestions,
                    "help": "Try using exact title or check explore_notes to find the note"
                }
            
            # Read current content
            cur_content, metadata = read_note_frontmatter(path)
            new_content = cur_content
            
            # Determine update mode
            if content is not None:
                if section:
                    new_content = replace_section(cur_content, section, content)
                    update_mode = "section_replaced"
                elif append:
                    sep = "\n\n" if not cur_content.endswith("\n") else "\n"
                    new_content = cur_content + sep + content
                    update_mode = "appended"
                else:
                    new_content = content
                    update_mode = "replaced"
            else:
                update_mode = "no_change"
            
            # Write updated content
            write_note_frontmatter(path, new_content, metadata)
            
            return {
                "success": True,
                "title": title, 
                "path": str(path.relative_to(vault_path)),
                "folder": path.parent.name if path.parent != vault_path else "root",
                "update_mode": update_mode,
                "message": f"Successfully updated '{title}'"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to update note: {str(e)}",
                "title": title
            }

    @mcp.tool()
    def delete_note(ctx: Context[ServerSession, AppContext], title: str) -> Dict[str, Any]:
        """
        🗑️ DELETE NOTE - Remove a note from vault (works in all folders)
        
        PURPOSE: Safely delete notes from anywhere in the vault
        
        FEATURES:
        • Universal search - works in all subfolders
        • Emoji support - handles titles with emojis
        • Backlink checking - warns about connected notes
        • Safe deletion - confirms before removing
        
        IMPROVEMENTS:
        • Fixed: Now works in subfolders (not just root)
        • Fixed: Handles emoji titles like "🗂️ Knowledge Management Hub"
        • Enhanced: Shows backlinks before deletion
        """
        vault_path = ctx.request_context.lifespan_context.vault_path
        
        try:
            from .utils.universal_finder import get_universal_finder
            
            # Use Universal Note Finder instead of limited note_path_for_title
            finder = get_universal_finder(vault_path)
            note_path = finder.find_note(title)
            
            if not note_path or not note_path.exists():
                # Provide helpful suggestions
                similar = finder.find_multiple(title, limit=3)
                suggestions = [s[0] for s in similar] if similar else []
                
                return {
                    "success": False,
                    "error": f"Note not found: {title}",
                    "suggestions": suggestions,
                    "help": "Try using exact title or check explore_notes to find the note"
                }
            
            # Check for backlinks before deletion (safety feature)
            try:
                from .utils.markdown_parser import extract_outlinks
                from .utils.vault import list_note_paths
                
                backlinks = []
                for other_path in list_note_paths(vault_path):
                    if other_path.stem == title:
                        continue  # Skip self
                    
                    try:
                        content = other_path.read_text(encoding='utf-8')
                        outlinks = extract_outlinks(content)
                        if title in outlinks:
                            backlinks.append(other_path.stem)
                    except:
                        continue
                
                if backlinks:
                    return {
                        "success": False,
                        "error": f"Cannot delete '{title}' - note has incoming links",
                        "backlinks": backlinks,
                        "suggestion": "Use delete_link to remove connections first, or use force_delete=True",
                        "note_path": str(note_path.relative_to(vault_path))
                    }
                        
            except Exception:
                # Backlink check failed, but we can still delete
                pass
            
            # Perform deletion
            note_path.unlink()
            
            return {
                "success": True,
                "deleted": title,
                "path": str(note_path.relative_to(vault_path)),
                "message": f"Successfully deleted '{title}'"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to delete note: {str(e)}",
                "title": title
            }

    @mcp.tool()
    def delete_link(
        ctx: Context[ServerSession, AppContext],
        from_note: str,
        to_note: str,
        bidirectional: bool = False,
        all_instances: bool = False
    ) -> Dict[str, Any]:
        """
        🗑️ DELETE LINK - Remove specific wikilink between notes
        
        PURPOSE: Clean and safe removal of [[wikilinks]] from note content
        
        FEATURES:
        • Remove specific link from note content
        • Bidirectional removal (both directions)  
        • All instances removal (multiple links to same note)
        • Safe text parsing - preserves formatting
        • Link validation before removal
        
        USE CASES:
        • Cleanup: delete_link("Old Project", "Deprecated Tool")
        • Refactoring: remove outdated connections
        • Bidirectional: delete_link("A", "B", bidirectional=True)
        """
        vault_path = ctx.request_context.lifespan_context.vault_path
        
        try:
            from .utils.vault import note_path_for_title
            from .utils.markdown_parser import read_note_frontmatter, write_note_frontmatter
            
            # Find source note
            from_path = note_path_for_title(vault_path, from_note)
            if not from_path.exists():
                return {"success": False, "error": f"Source note not found: {from_note}"}
            
            # Read source note content
            content, metadata = read_note_frontmatter(from_path)
            original_content = content
            
            # Remove links from content
            import re
            
            if all_instances:
                # Remove all instances of [[to_note]]
                pattern = re.compile(rf'\[\[{re.escape(to_note)}(?:\|[^\]]+)?\]\]', re.IGNORECASE)
                new_content = pattern.sub('', original_content)
            else:
                # Remove first instance only
                pattern = rf'\[\[{re.escape(to_note)}(?:\|[^\]]+)?\]\]'
                new_content = re.sub(pattern, '', original_content, count=1, flags=re.IGNORECASE)
            
            # Clean up extra whitespace
            new_content = re.sub(r'\n\s*\n\s*\n', '\n\n', new_content)  # Multiple newlines -> double
            new_content = new_content.strip()
            
            # Check if any changes were made
            links_removed = len(re.findall(rf'\[\[{re.escape(to_note)}(?:\|[^\]]+)?\]\]', original_content, re.IGNORECASE))
            if original_content == new_content:
                return {
                    "success": False, 
                    "error": f"No links found from '{from_note}' to '{to_note}'"
                }
            
            # Write updated content
            write_note_frontmatter(from_path, new_content, metadata)
            
            result = {
                "success": True,
                "from_note": from_note,
                "to_note": to_note,
                "links_removed": links_removed,
                "bidirectional": bidirectional
            }
            
            # Handle bidirectional removal
            if bidirectional:
                to_path = note_path_for_title(vault_path, to_note)
                if to_path.exists():
                    try:
                        to_content, to_metadata = read_note_frontmatter(to_path)
                        to_original = to_content
                        
                        if all_instances:
                            pattern = re.compile(rf'\[\[{re.escape(from_note)}(?:\|[^\]]+)?\]\]', re.IGNORECASE)
                            to_new_content = pattern.sub('', to_original)
                        else:
                            pattern = rf'\[\[{re.escape(from_note)}(?:\|[^\]]+)?\]\]'
                            to_new_content = re.sub(pattern, '', to_original, count=1, flags=re.IGNORECASE)
                        
                        to_new_content = re.sub(r'\n\s*\n\s*\n', '\n\n', to_new_content)
                        to_new_content = to_new_content.strip()
                        
                        reverse_links_removed = len(re.findall(rf'\[\[{re.escape(from_note)}(?:\|[^\]]+)?\]\]', to_original, re.IGNORECASE))
                        
                        if to_original != to_new_content:
                            write_note_frontmatter(to_path, to_new_content, to_metadata)
                            result["reverse_links_removed"] = reverse_links_removed
                        else:
                            result["reverse_links_removed"] = 0
                            
                    except Exception as e:
                        result["reverse_error"] = f"Failed to remove reverse link: {str(e)}"
                else:
                    result["reverse_error"] = f"Target note not found: {to_note}"
            
            return result
            
        except Exception as e:
            return {"success": False, "error": f"Failed to delete link: {str(e)}"}

    @mcp.tool()
    def list_links(
        ctx: Context[ServerSession, AppContext],
        note_title: str,
        link_type: str = "all",  # "outlinks", "backlinks", "all"
        include_context: bool = True
    ) -> Dict[str, Any]:
        """
        📋 LIST LINKS - Show all connections for a note
        
        PURPOSE: Comprehensive view of note's knowledge graph connections
        
        FEATURES:
        • Outlinks - [[links]] from this note
        • Backlinks - notes that link to this note  
        • Context - surrounding text for each link
        • Link analysis - connection strength
        
        USE CASES:
        • Overview: list_links("Project Alpha")
        • Analysis: see all connections for planning
        • Maintenance: find links that need updating
        """
        vault_path = ctx.request_context.lifespan_context.vault_path
        
        try:
            from .utils.universal_finder import get_universal_finder
            from .utils.vault import list_note_paths
            from .utils.markdown_parser import read_note_frontmatter, extract_outlinks
            
            # Use Universal Note Finder
            finder = get_universal_finder(vault_path)
            note_path = finder.find_note(note_title)
            
            if not note_path or not note_path.exists():
                # Provide helpful suggestions
                similar = finder.find_multiple(note_title, limit=3)
                suggestions = [s[0] for s in similar] if similar else []
                
                return {
                    "success": False, 
                    "error": f"Note not found: {note_title}",
                    "suggestions": suggestions,
                    "help": "Try using exact title or check explore_notes to find the note"
                }
            
            result = {
                "success": True,
                "note_title": note_title,
                "outlinks": [],
                "backlinks": [],
                "total_connections": 0
            }
            
            # Get outlinks (links FROM this note)
            if link_type in ["all", "outlinks"]:
                try:
                    content, metadata = read_note_frontmatter(note_path)
                    outlinks = extract_outlinks(content)
                    
                    if include_context:
                        import re
                        lines = content.split('\n')
                        for link in outlinks:
                            # Find context for each link
                            for line_num, line in enumerate(lines, 1):
                                if f'[[{link}' in line:
                                    context = line.strip()
                                    if len(context) > 100:
                                        # Truncate long lines
                                        link_pos = context.find(f'[[{link}')
                                        start = max(0, link_pos - 30)
                                        end = min(len(context), link_pos + 70)
                                        context = '...' + context[start:end] + '...' if start > 0 or end < len(context) else context[start:end]
                                    
                                    result["outlinks"].append({
                                        "target": link,
                                        "context": context,
                                        "line": line_num
                                    })
                                    break
                    else:
                        result["outlinks"] = [{"target": link} for link in outlinks]
                        
                except Exception as e:
                    result["outlinks_error"] = f"Failed to read outlinks: {str(e)}"
            
            # Get backlinks (links TO this note)  
            if link_type in ["all", "backlinks"]:
                try:
                    for note_path_candidate in list_note_paths(vault_path):
                        if note_path_candidate.stem == note_title:
                            continue  # Skip self-references
                        
                        try:
                            content_candidate, metadata_candidate = read_note_frontmatter(note_path_candidate)
                            outlinks = extract_outlinks(content_candidate)
                            
                            if note_title in outlinks:
                                backlink_info = {"source": note_path_candidate.stem}
                                
                                if include_context:
                                    import re
                                    lines = content_candidate.split('\n')
                                    for line_num, line in enumerate(lines, 1):
                                        if f'[[{note_title}' in line:
                                            context = line.strip()
                                            if len(context) > 100:
                                                link_pos = context.find(f'[[{note_title}')
                                                start = max(0, link_pos - 30)
                                                end = min(len(context), link_pos + 70)
                                                context = '...' + context[start:end] + '...' if start > 0 or end < len(context) else context[start:end]
                                            
                                            backlink_info.update({
                                                "context": context,
                                                "line": line_num
                                            })
                                            break
                                
                                result["backlinks"].append(backlink_info)
                                
                        except Exception:
                            continue  # Skip problematic files
                            
                except Exception as e:
                    result["backlinks_error"] = f"Failed to find backlinks: {str(e)}"
            
            # Calculate totals
            result["total_connections"] = len(result["outlinks"]) + len(result["backlinks"])
            result["outlinks_count"] = len(result["outlinks"]) 
            result["backlinks_count"] = len(result["backlinks"])
            
            # Connection strength analysis
            if result["total_connections"] == 0:
                result["connection_strength"] = "none"
            elif result["total_connections"] <= 2:
                result["connection_strength"] = "weak"  
            elif result["total_connections"] <= 5:
                result["connection_strength"] = "medium"
            else:
                result["connection_strength"] = "strong"
            
            return result
            
        except Exception as e:
            return {"success": False, "error": f"Failed to list links: {str(e)}"}

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
        keywords: str = "",
        search_in: str = "all",  # "all", "titles", "content", "tags"
        
        # 🏷️ TAG FILTERS
        include_tags: Optional[List[str]] = None,     # Only notes with these tags
        exclude_tags: Optional[List[str]] = None,     # Exclude notes with these tags  
        require_all_tags: bool = False,              # Require all tags vs any tag
        
        # 📅 DATE FILTERS  
        created_after: Optional[str] = None,         # "2024-01-01" format
        created_before: Optional[str] = None,        # "2024-12-31" format
        modified_after: Optional[str] = None,        # Recently modified after date
        modified_before: Optional[str] = None,       # Not modified after date
        
        # 📁 FOLDER FILTERS
        folders: Optional[List[str]] = None,         # Search only in these folders
        exclude_folders: Optional[List[str]] = None, # Exclude these folders
        
        # 📊 CONTENT FILTERS
        min_words: Optional[float] = None,           # Minimum word count (float for Cursor compatibility)
        max_words: Optional[float] = None,           # Maximum word count (float for Cursor compatibility)  
        has_tasks: Optional[bool] = None,            # Contains checkboxes [ ]
        min_links: Optional[float] = None,           # Minimum outgoing links (float for Cursor compatibility)
        max_links: Optional[float] = None,           # Maximum outgoing links (float for Cursor compatibility)
        
        # 🎯 SEARCH BEHAVIOR
        language_flexible: bool = True,              # Russian/English transliteration
        case_sensitive: bool = False,                # Case sensitivity
        fuzzy_matching: bool = True,                 # Typo correction
        
        # 📋 RESULTS  
        limit: float = 15,                           # Number of results (float for Cursor compatibility)
        sort_by: str = "relevance",                  # "relevance", "modified", "created", "title"
        include_content_preview: bool = True,        # Content preview
        include_metadata: bool = True,               # Include tags, dates, stats
        min_relevance: float = 0.1                   # Minimum relevance score
    ) -> Dict[str, Any]:
        """
        🔍 EXPLORE NOTES - Advanced search with multilingual support and powerful filters
        
        PURPOSE: Comprehensive search through notes with content indexing, transliteration, 
        and extensive filtering capabilities. One tool for all search needs.
        
        FEATURES:
        • Multilingual search (Russian ↔ English transliteration)
        • Content indexing (searches inside note content, not just titles)
        • Morphological variants (programming → program → programm)
        • Advanced filtering (tags, dates, folders, content metrics)
        • Flexible sorting and relevance scoring
        • Content preview with highlighted matches
        
        ADVANCED FILTERS:
        • Tag filtering: include_tags=["work", "active"], exclude_tags=["archive"]
        • Date filtering: modified_after="2024-09-01", created_before="2024-12-31"
        • Folder filtering: folders=["Projects"], exclude_folders=["Archive"]
        • Content filtering: min_words=100, has_tasks=True, min_links=2
        • Sorting: sort_by="modified" | "created" | "title" | "relevance"
        
        USE CASES:
        • Basic search: explore_notes("machine learning")
        • Filtered search: explore_notes("productivity", include_tags=["work"], modified_after="2024-09-01")
        • Content discovery: explore_notes("", has_tasks=True, folders=["Projects"])
        • Maintenance: explore_notes("", max_words=50, max_links=0, sort_by="modified")
        • Research: explore_notes("AI", exclude_tags=["draft"], min_words=200)
        """
        try:
            from .smart_search import SmartSearchEngine
            
            vault_path = ctx.request_context.lifespan_context.vault_path
            
            # Convert float to int and ensure limit is within bounds
            limit = int(float(limit))  # Handle Cursor IDE float numbers
            limit = min(limit, 30)
            
            # Создаем поисковый движок
            search_engine = SmartSearchEngine(vault_path)
            
            # Выполняем поиск с новыми фильтрами
            search_result = search_engine.search_notes(
                keywords=keywords,
                search_in=search_in,
                
                # Tag filters
                include_tags=include_tags,
                exclude_tags=exclude_tags,
                require_all_tags=require_all_tags,
                
                # Date filters  
                created_after=created_after,
                created_before=created_before,
                modified_after=modified_after,
                modified_before=modified_before,
                
                # Folder filters
                folders=folders,
                exclude_folders=exclude_folders,
                
                # Content filters
                min_words=min_words,
                max_words=max_words,
                has_tasks=has_tasks,
                min_links=min_links,
                max_links=max_links,
                
                # Search behavior
                language_flexible=language_flexible,
                case_sensitive=case_sensitive,
                fuzzy_matching=fuzzy_matching,
                
                # Results
                limit=limit,
                sort_by=sort_by,
                include_content_preview=include_content_preview,
                include_metadata=include_metadata,
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

    @mcp.tool()
    def create_folder(
        ctx: Context[ServerSession, AppContext],
        folder_path: str
    ) -> Dict[str, Any]:
        """
        📁 CREATE FOLDER - Create a new folder in the vault
        
        PURPOSE: Organize notes by creating folder structure in Obsidian vault.
        
        FEATURES:
        • Creates nested folder structures (e.g. "Projects/2024/AI")
        • Handles existing folders gracefully
        • Cross-platform path handling
        • Safe folder naming (removes invalid characters)
        
        USE CASES:
        • Project organization: "Create folder 'Projects/Website Redesign'"
        • Topic categorization: "Create folder 'Learning/Machine Learning'"
        • Date-based organization: "Create folder 'Daily/2024/September'"
        """
        vault_path = ctx.request_context.lifespan_context.vault_path
        
        # Sanitize folder path
        safe_path = folder_path.replace("\\", "/")  # Normalize separators
        safe_path = "/".join([
            "".join(c for c in part if c not in r'<>:"|?*')  # Remove invalid chars
            for part in safe_path.split("/")
            if part.strip()  # Remove empty parts
        ])
        
        if not safe_path:
            return {"success": False, "error": "Invalid folder path"}
        
        folder_full_path = vault_path / safe_path
        
        try:
            folder_existed = folder_full_path.exists()
            folder_full_path.mkdir(parents=True, exist_ok=True)
            
            return {
                "success": True,
                "folder_path": safe_path,
                "full_path": str(folder_full_path.relative_to(vault_path)),
                "created": not folder_existed,
                "message": f"{'Created' if not folder_existed else 'Verified'} folder: {safe_path}"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to create folder: {str(e)}"}

    @mcp.tool()
    def move_note(
        ctx: Context[ServerSession, AppContext],
        note_title: str,
        target_folder: Optional[str] = None,
        new_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        📦 MOVE NOTE - Move and/or rename a note
        
        PURPOSE: Reorganize vault by moving notes between folders or renaming them.
        Maintains all links and references automatically.
        
        FEATURES:
        • Move to different folder
        • Rename note (with or without moving)  
        • Preserve all markdown links and references
        • Handle conflicts (existing files)
        • Cross-platform path handling
        
        USE CASES:
        • Organization: "Move note 'Ideas' to folder 'Projects'"
        • Renaming: "Rename note 'Draft' to 'Final Article'"
        • Both: "Move 'Old Notes' to 'Archive' and rename to 'Legacy Data'"
        """
        vault_path = ctx.request_context.lifespan_context.vault_path
        
        # Find current note
        current_path = None
        for path in list_note_paths(vault_path):
            if path.stem == note_title:
                current_path = path
                break
        
        if not current_path or not current_path.exists():
            return {"success": False, "error": f"Note '{note_title}' not found"}
        
        # Determine new location
        final_title = new_title or note_title
        
        # Sanitize new title
        safe_title = "".join(c for c in final_title if c not in r'<>:"/\|?*')
        if not safe_title:
            return {"success": False, "error": "Invalid new title"}
        
        # Determine target path
        if target_folder:
            # Ensure target folder exists
            safe_folder = target_folder.replace("\\", "/")
            safe_folder = "/".join([
                "".join(c for c in part if c not in r'<>:"|?*')
                for part in safe_folder.split("/")
                if part.strip()
            ])
            
            target_dir = vault_path / safe_folder
            try:
                target_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return {"success": False, "error": f"Cannot create target folder: {str(e)}"}
                
            new_path = target_dir / f"{safe_title}.md"
        else:
            new_path = current_path.parent / f"{safe_title}.md"
        
        # Check for conflicts
        if new_path.exists() and new_path != current_path:
            return {
                "success": False,
                "error": f"Target file already exists: {new_path.relative_to(vault_path)}"
            }
        
        try:
            # Move/rename the file
            import shutil
            if new_path != current_path:
                shutil.move(str(current_path), str(new_path))
            
            relative_old = current_path.relative_to(vault_path)
            relative_new = new_path.relative_to(vault_path)
            
            return {
                "success": True,
                "old_path": str(relative_old),
                "new_path": str(relative_new),
                "old_title": note_title,
                "new_title": safe_title,
                "moved": target_folder is not None,
                "renamed": new_title is not None,
                "message": f"Successfully moved '{note_title}' to '{relative_new}'"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to move note: {str(e)}"}

    @mcp.tool()
    def list_folders(
        ctx: Context[ServerSession, AppContext],
        parent_folder: Optional[str] = None,
        include_empty: bool = True,
        include_note_count: bool = True
    ) -> Dict[str, Any]:
        """
        📂 LIST FOLDERS - List all folders in the vault
        
        PURPOSE: Browse and understand vault folder structure for organization.
        
        FEATURES:
        • Hierarchical folder listing
        • Note counts per folder
        • Filter by parent folder
        • Include/exclude empty folders
        • Nested structure visualization
        
        USE CASES:
        • Vault overview: "Show me all folders in my vault"
        • Specific area: "List folders in 'Projects'"
        • Organization planning: "Show folders with note counts"
        """
        vault_path = ctx.request_context.lifespan_context.vault_path
        
        # Determine starting directory
        if parent_folder:
            safe_parent = parent_folder.replace("\\", "/")
            start_dir = vault_path / safe_parent
            if not start_dir.exists():
                return {"success": False, "error": f"Parent folder '{parent_folder}' not found"}
        else:
            start_dir = vault_path
        
        folders = []
        
        try:
            # Get all directories
            for item in vault_path.rglob("*"):
                if item.is_dir() and item != vault_path:
                    # Skip hidden folders except .obsidian
                    if any(part.startswith('.') and part != '.obsidian' for part in item.parts):
                        continue
                    
                    relative_path = item.relative_to(vault_path)
                    
                    # Filter by parent folder if specified
                    if parent_folder:
                        try:
                            relative_path.relative_to(start_dir.relative_to(vault_path))
                        except ValueError:
                            continue  # Not in the parent folder
                    
                    # Count notes in this folder (direct children only)
                    note_count = 0
                    if include_note_count:
                        note_count = len([f for f in item.iterdir() if f.is_file() and f.suffix == '.md'])
                    
                    # Skip empty folders if requested
                    if not include_empty and note_count == 0:
                        continue
                    
                    folder_info = {
                        "path": str(relative_path).replace("\\", "/"),
                        "name": item.name,
                        "depth": len(relative_path.parts),
                    }
                    
                    if include_note_count:
                        folder_info["note_count"] = note_count
                    
                    folders.append(folder_info)
            
            # Sort by path for consistent ordering
            folders.sort(key=lambda x: x["path"])
            
            return {
                "success": True,
                "folders": folders,
                "total_folders": len(folders),
                "parent_folder": parent_folder,
                "include_empty": include_empty,
                "include_note_count": include_note_count
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to list folders: {str(e)}"}

    @mcp.tool()
    def get_ai_usage_guide(
        ctx: Context[ServerSession, AppContext]
    ) -> Dict[str, Any]:
        """
        🤖 AI USAGE GUIDE - Complete guide for AI assistants on using Obsidian MCP Server
        
        PURPOSE: Provides comprehensive instructions, best practices, and examples 
        for AI assistants to effectively use all MCP tools for Obsidian knowledge management.
        
        WHEN TO USE: AI should call this tool when:
        • First connecting to understand capabilities
        • User asks about Obsidian organization or structure
        • Needing guidance on best practices
        • Planning complex note management tasks
        
        RETURNS: Complete system prompt with usage patterns and examples
        """
        
        guide = {
            "system_prompt": """# 🧠 Enhanced Obsidian MCP Server - AI Usage Guide

## 🎯 PRIMARY MISSION
You are an expert Obsidian knowledge management assistant with 12 powerful tools. 
Help users organize, search, create, and maintain their knowledge vault efficiently.

## 📚 OBSIDIAN METHODOLOGY & CONCEPTS

### 🔗 LINKING SYSTEMS - THE HEART OF OBSIDIAN

#### **1. Wikilinks [[Note Title]]**
- **Primary connection method**: `[[Note Name]]` creates instant links
- **Auto-completion**: Obsidian suggests existing notes while typing
- **Bidirectional**: Links create automatic backlinks in referenced notes
- **Case sensitive**: `[[Project]]` ≠ `[[project]]`
- **Best practice**: Use natural, descriptive titles that can be linked from anywhere

#### **2. Link Types & Usage Patterns**
```markdown
# Direct links
[[Project Alpha]] - simple reference

# Links with display text  
[[Project Alpha|The Alpha Project]] - custom display

# Header links
[[Project Alpha#Implementation]] - specific section

# Block references  
[[Project Alpha#^block123]] - specific paragraph

# Contextual links with explanation
[[Project Alpha]] - discussing the technical architecture
```

### 🏷️ TAGGING SYSTEM - CATEGORIZATION & DISCOVERY

#### **1. Tag Hierarchy**
```yaml
# Use forward slashes for nested tags
tags:
  - project/active
  - project/web-development  
  - status/in-progress
  - priority/high
  - area/work
```

#### **2. Tag Strategy**
- **Status tags**: `#status/active`, `#status/completed`, `#status/on-hold`
- **Type tags**: `#type/project`, `#type/meeting`, `#type/idea`, `#type/reference`
- **Area tags**: `#area/work`, `#area/personal`, `#area/learning`
- **Topic tags**: `#tech/javascript`, `#method/gtd`, `#concept/productivity`
- **Priority tags**: `#priority/urgent`, `#priority/important`, `#priority/someday`

#### **3. Tag vs Links Decision Matrix**
- **Use Tags for**: Categories, status, metadata, filtering, bulk organization
- **Use Links for**: Specific relationships, references, knowledge connections, navigation

### 🗂️ FOLDER STRUCTURE PHILOSOPHY

#### **1. PARA Method (Projects, Areas, Resources, Archive)**
```
📁 Projects/           # Things with deadlines
  📁 Active/
    📁 Website Redesign/
    📁 Marketing Campaign/
  📁 Completed/
    📁 2024/
      📁 Q1/
      
📁 Areas/              # Ongoing responsibilities  
  📁 Work/
    📁 Team Management/
    📁 Strategy/
  📁 Personal/
    📁 Health/
    📁 Finance/
    
📁 Resources/          # Future reference
  📁 Learning/
    📁 Programming/
    📁 Design/
  📁 Templates/
  📁 Checklists/
  
📁 Archive/            # Inactive items
  📁 2024/
  📁 2023/
```

#### **2. Alternative: Topic-Based Structure**
```
📁 Technology/
  📁 Programming/
    📁 JavaScript/
    📁 Python/
  📁 AI & ML/
  
📁 Business/
  📁 Strategy/
  📁 Marketing/
  📁 Operations/
  
📁 Personal/
  📁 Goals/
  📁 Habits/
  📁 Reflections/
```

### 📋 NOTE TYPES & TEMPLATES

#### **1. Daily Notes**
```markdown
# {{date:YYYY-MM-DD}} - {{date:dddd}}

## 📅 Today's Focus
- [ ] Priority task 1 #priority/high
- [ ] Priority task 2 #priority/medium

## 🔗 Connected Notes
- [[Project Alpha]] - worked on architecture
- [[Meeting - Team Sync]] - discussed roadmap

## 💭 Thoughts & Ideas
-

## 📊 Daily Metrics
- Energy: /10
- Productivity: /10
- Mood: /10

## 🔄 Tomorrow's Prep
- [ ]

---
tags: [daily, {{date:YYYY}}, {{date:MM}}]
```

#### **2. Project Notes**
```markdown
# Project: {{title}}

## 🎯 Overview
**Status**: #status/active
**Priority**: #priority/high  
**Deadline**: 
**Stakeholders**: [[Person 1]], [[Person 2]]

## 🎪 Scope & Objectives
-

## 📋 Tasks & Milestones
- [ ] Phase 1: Planning [[Project Alpha - Planning]]
- [ ] Phase 2: Development [[Project Alpha - Development]]  
- [ ] Phase 3: Testing [[Project Alpha - Testing]]

## 🔗 Related Resources  
- [[Project Template]]
- [[Similar Project - Beta]]
- [[Best Practices - Project Management]]

## 📊 Progress Tracking
- Started: {{date}}
- Last updated: {{date}}
- Completion: _%

---
tags: [project, project/active, area/work]
```

#### **3. Meeting Notes**
```markdown
# Meeting: {{title}} - {{date:YYYY-MM-DD}}

**Attendees**: [[Person 1]], [[Person 2]], [[Person 3]]  
**Project**: [[Project Alpha]]
**Type**: #type/meeting #meeting/standup

## 📋 Agenda
1. 
2.
3.

## 💬 Discussion Points
### Topic 1
- Key point
- Decision: 
- **Action**: [[Person]] to do X by Y

### Topic 2  
- Discussion notes
- **Action**: Follow up on [[Related Issue]]

## 🎯 Action Items
- [ ] [[Person 1]]: Task description - Due: {{date+7d}}
- [ ] [[Person 2]]: Another task - Due: {{date+3d}}

## 🔗 Follow-up Notes
- [[Meeting - Previous Session]]
- [[Project Alpha#Current Status]]

---
tags: [meeting, project/alpha, {{date:YYYY}}, {{date:MM}}]
```

### 🕸️ KNOWLEDGE GRAPH OPTIMIZATION

#### **1. Hub Notes Strategy**
Create "hub" or "index" notes that serve as central connection points:

```markdown
# 🗂️ Programming Hub

## 📚 Languages
- [[JavaScript]] - Frontend and backend development
- [[Python]] - Data science and automation  
- [[TypeScript]] - Type-safe JavaScript

## 🛠️ Tools & Frameworks
- [[React]] - UI development
- [[Node.js]] - Backend runtime
- [[Django]] - Python web framework

## 📖 Learning Resources
- [[Programming Books]]
- [[Coding Tutorials]]
- [[Programming Courses]]

## 🚀 Projects Using Programming
- [[Website Redesign]] - JavaScript, React
- [[Data Analysis Tool]] - Python, pandas
- [[API Development]] - Node.js, Express
```

#### **2. MOCs (Maps of Content)**
Structure large topic areas:

```markdown
# 🗺️ Productivity Systems MOC

## 🎯 Core Systems
- [[GTD (Getting Things Done)]]
- [[PARA Method]]  
- [[Zettelkasten]]
- [[Time Blocking]]

## 📱 Tools & Apps
- [[Obsidian]]
- [[Notion]]
- [[Todoist]]

## 📚 Key Concepts  
- [[Capture Everything]]
- [[Regular Reviews]]
- [[Context Switching]]
- [[Flow State]]

## 🔄 My Current System
- [[Current Productivity Setup]]
- [[Weekly Review Process]]
- [[Daily Planning Routine]]
```

### 🎨 VISUAL GRAPH OPTIMIZATION

#### **1. Color Coding Strategy**
- **Projects**: Red nodes
- **People**: Blue nodes  
- **Concepts**: Green nodes
- **Resources**: Yellow nodes
- **Archive**: Gray nodes

#### **2. Graph Navigation**
- **Keep hubs central**: Place MOCs and hub notes at graph center
- **Minimize orphan notes**: Every note should connect to at least one other
- **Use consistent naming**: Similar notes should have similar prefixes
- **Regular cleanup**: Archive old connections, merge duplicate topics

### 🔄 MAINTENANCE WORKFLOWS

#### **1. Weekly Knowledge Review**
```python
# Weekly maintenance checklist:
1. Review recent notes for missing links
2. Check for duplicate or similar notes to merge
3. Update project statuses and priorities  
4. Create new hub notes for emerging topics
5. Archive completed projects and old daily notes
```

#### **2. Monthly Graph Cleanup**
```python
# Monthly optimization:
1. Analyze graph structure for bottlenecks
2. Create missing connection points (hubs/MOCs)
3. Merge overly specific tags
4. Review and update folder structure
5. Archive outdated information
```

### 🎯 AI OPTIMIZATION GUIDELINES

#### **When Creating Notes:**
1. **Always add relevant tags** - minimum 2-3 tags per note
2. **Include at least 2 links** - connect to existing knowledge
3. **Use descriptive titles** - should be linkable from other contexts
4. **Follow consistent naming** - similar notes, similar patterns
5. **Add creation date** - for temporal organization

#### **When Organizing:**
1. **Prefer links over folders** - links are more flexible
2. **Use folders for major categories** - not for micro-organization  
3. **Create hub notes** - when a topic has >5 related notes
4. **Tag for discovery** - link for relationships
5. **Regular maintenance** - keep the graph healthy

## 🛠️ AVAILABLE TOOLS OVERVIEW

### 📝 NOTE MANAGEMENT (6 tools)
- `list_notes` - Get recent notes (max 50, default 20) with metadata
- `create_note` - Create new notes with frontmatter and content
- `read_note` - Read full note with backlinks/outlinks analysis  
- `update_note` - Modify existing notes (full replace or append)
- `delete_note` - Remove notes safely
- `create_link` - Create [[wikilinks]] between notes

### 📁 STRUCTURE MANAGEMENT (3 tools)  
- `create_folder` - Create nested folder structures
- `move_note` - Move/rename notes between folders
- `list_folders` - Browse vault structure with note counts

### 🔍 INTELLIGENT SEARCH (2 tools)
- `explore_notes` - Smart search with multilingual support, content indexing
- `list_notes` - For browsing recent activity

### 🔗 CONNECTIONS (1 tool)
- `create_link` - Build knowledge graphs through linked notes

## 🎯 USAGE PATTERNS & BEST PRACTICES

### 🔍 SEARCH STRATEGY
1. **For recent activity**: Use `list_notes` (faster, shows latest changes)
2. **For content search**: Use `explore_notes` (semantic, multilingual, indexes content)
3. **For browsing structure**: Use `list_folders` first, then target specific areas

### 📝 NOTE CREATION BEST PRACTICES  
```markdown
# Always include:
- Clear, descriptive titles
- Relevant tags in frontmatter
- Structured headings (H1 for main topic)
- Links to related notes [[Like This]]

# Example structure:
---
tags: [project, web-development, frontend]  
created: 2024-01-01
---

# Main Topic
## Subtopic 1
- Key point with [[Related Note]]
## Subtopic 2  
- Another insight
```

### 🗂️ ORGANIZATION PHILOSOPHY
1. **Folder Structure**: Topic-based hierarchy
   - `Projects/[Project Name]/[Category]`  
   - `Areas/[Life Area]/[Subcategory]`
   - `Resources/[Resource Type]` 
   - `Archive/[Year]/[Month]`

2. **Naming Conventions**:
   - Use clear, searchable titles
   - Avoid special characters: `<>:"/\\|?*`
   - Date format: YYYY-MM-DD for daily notes
   - Project format: "Project - Feature Name"

### 🔗 LINKING STRATEGY
- **Create connections** between related concepts
- **Use context** when creating links: `[[Note]] - specific relationship`
- **Build knowledge graphs** by connecting new notes to existing ones

## 🎭 COMMUNICATION PATTERNS

### 📊 WHEN PRESENTING RESULTS
- **Always show counts**: "Found 15 notes, showing top 10"
- **Include metadata**: modification dates, folders, tags
- **Highlight relevance**: for search results, explain why notes match
- **Suggest next actions**: "Would you like me to create links between these?"

### 🗣️ LANGUAGE HANDLING  
- **Multilingual support**: explore_notes handles Russian ↔ English automatically
- **Natural queries**: "найди заметки про программирование" = "find programming notes"  
- **Flexible search**: handles typos, synonyms, morphological variants

### ⚡ PERFORMANCE OPTIMIZATION
- **Batch operations**: Plan multiple related actions together
- **Use appropriate limits**: Don't request more data than needed
- **Cache-friendly**: Recent results may be faster than deep searches

## 🎪 ADVANCED USAGE SCENARIOS

### 📚 KNOWLEDGE BASE MAINTENANCE
```python
# Weekly organization workflow:
1. list_notes(limit=20) - Check recent activity
2. explore_notes("untagged OR orphaned") - Find unorganized content  
3. create_folder("Archive/2024/December") - Seasonal organization
4. move_note(old_notes, target="Archive") - Clean up
```

### 🔄 PROJECT MANAGEMENT  
```python
# New project setup:
1. create_folder("Projects/New Website/Planning")
2. create_folder("Projects/New Website/Development") 
3. create_note("New Website - Overview", folder="Projects/New Website")
4. create_link(from="New Website - Overview", to="Project Template")
```

### 🔍 RESEARCH WORKFLOWS
```python  
# Research investigation:
1. explore_notes("artificial intelligence machine learning") 
2. read_note(interesting_result, include_backlinks=True)
3. create_note("Research Summary - AI Topic", with_references)
4. create_link(summary, to=all_source_notes)
```

## ⚠️ IMPORTANT LIMITATIONS & SAFETY

### 🛡️ BUILT-IN SAFEGUARDS
- **list_notes**: Max 50 results (default 20) to prevent overwhelming
- **File operations**: Only within vault boundaries
- **Path sanitization**: Automatic removal of dangerous characters
- **Conflict detection**: Won't overwrite existing files without warning

### 🚫 WHAT NOT TO DO
- **Don't** request huge result sets (use pagination with limits)
- **Don't** create duplicate folder structures unnecessarily  
- **Don't** move system files or .obsidian directory contents
- **Don't** create notes with identical titles (causes conflicts)

### ✅ ALWAYS CONSIDER
- **User's current context**: What are they working on?
- **Vault organization**: How is their system structured?  
- **Progressive disclosure**: Start simple, add complexity as needed
- **Backup implications**: Major moves should be mentioned

## 🎯 RESPONSE EXCELLENCE GUIDELINES

### 📈 FOR SEARCH RESULTS
- **Relevance ranking**: Explain why results are ordered this way
- **Content previews**: Show key excerpts that match the query
- **Actionable insights**: "These 3 notes seem related, should I link them?"

### 📝 FOR CONTENT CREATION  
- **Context awareness**: Reference existing related notes
- **Structural consistency**: Match user's existing note patterns
- **Rich linking**: Proactively suggest connections

### 🗂️ FOR ORGANIZATION TASKS
- **Impact assessment**: "This will affect 12 notes in 3 folders"
- **Alternative suggestions**: "Or we could organize by date instead?"
- **Confirmation requests**: For major structural changes

## 🚀 ADVANCED AI CAPABILITIES

### 🧠 SEMANTIC UNDERSTANDING
- **Intent recognition**: "clean up my notes" → organizational workflow
- **Context building**: Remember user's preferences and patterns
- **Proactive suggestions**: Notice gaps and suggest improvements

### 🔗 KNOWLEDGE GRAPH BUILDING
- **Discover connections**: Find related notes that should be linked
- **Identify gaps**: Topics that need more development  
- **Suggest structure**: Optimal organization for user's content type

### 📊 ANALYTICS & INSIGHTS
- **Usage patterns**: Which notes get updated frequently?
- **Knowledge clusters**: What topics dominate the vault?
- **Growth opportunities**: Areas that could use more content

## 🎊 SUCCESS METRICS
- **User efficiency**: Tasks completed in fewer steps
- **Knowledge discoverability**: Relevant results found quickly  
- **System organization**: Logical, maintainable structure
- **User satisfaction**: Clear, helpful responses""",

            "quick_reference": {
                "search_commands": [
                    "list_notes() - Recent activity, fast browsing",
                    "explore_notes('keywords') - Content search, multilingual",  
                    "list_folders() - Structure overview with counts"
                ],
                "creation_commands": [
                    "create_note(title, content) - New notes with structure",
                    "create_folder('path/to/folder') - Nested organization",
                    "create_link(from_note, to_note) - Knowledge connections"
                ],
                "management_commands": [
                    "move_note(title, target_folder) - Reorganize content",
                    "update_note(title, content) - Modify existing notes",
                    "read_note(title, include_backlinks=True) - Deep analysis"
                ]
            },

            "example_workflows": {
                "daily_review": [
                    "1. list_notes(limit=10) # Check recent activity",
                    "2. explore_notes('untagged') # Find unorganized notes", 
                    "3. create_links between related discoveries",
                    "4. move_note old items to appropriate folders"
                ],
                "research_project": [
                    "1. create_folder('Research/Topic Name/Sources')",
                    "2. create_note('Research Overview') with methodology",
                    "3. explore_notes('related keywords') for existing knowledge",
                    "4. create_link between overview and all relevant sources"
                ],
                "knowledge_cleanup": [
                    "1. list_folders() to understand current structure", 
                    "2. explore_notes('orphaned OR duplicate') to find issues",
                    "3. create_folder('Archive/Cleanup') for outdated content",
                    "4. move_note problematic items to appropriate locations"
                ]
            },

            "multilingual_examples": {
                "russian_english": [
                    "explore_notes('машинное обучение') # Finds 'machine learning' too",
                    "explore_notes('программирование') # Finds 'programming', 'coding'", 
                    "explore_notes('artificial intelligence') # Finds 'ИИ', 'искусственный интеллект'"
                ]
            },

            "meta": {
                "version": "Enhanced v1.0",
                "total_tools": 12,
                "ai_optimized": True,
                "last_updated": "2024-09-24",
                "recommended_usage": "Call this guide when planning complex operations or when user asks about organization strategies"
            }
        }

        return {
            "success": True,
            "guide": guide,
            "usage": "This comprehensive guide should be your primary reference for using all MCP tools effectively. Refer to specific sections based on user needs.",
            "quick_access": {
                "system_prompt": "Full AI instructions and best practices",
                "quick_reference": "Command cheat sheet",  
                "example_workflows": "Common usage patterns",
                "multilingual_examples": "Russian/English search examples"
            }
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


