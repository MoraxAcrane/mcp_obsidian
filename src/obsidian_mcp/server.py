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


