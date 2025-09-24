# 🔗 Enhanced Link Management Tools

## 🎯 Проблема
**Асимметрия в API управления связями:**
- ✅ `create_link` - простое создание [[wikilinks]]
- ❌ `delete_link` - НЕТ инструмента, нужно manual editing
- ❌ `list_links` - нет удобного просмотра всех связей
- ❌ `update_link` - нет изменения существующих связей

## 🚀 Решение: Comprehensive Link Management

### 1. 🗑️ `delete_link` - Удаление связей
```python
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
```

### 2. 📋 `list_links` - Просмотр всех связей
```python
@mcp.tool()
def list_links(
    ctx: Context[ServerSession, AppContext],
    note_title: str,
    link_type: str = "all",  # "outlinks", "backlinks", "all"
    include_context: bool = True,
    group_by_target: bool = False
) -> Dict[str, Any]:
    """
    📋 LIST LINKS - Show all connections for a note
    
    PURPOSE: Comprehensive view of note's knowledge graph connections
    
    FEATURES:
    • Outlinks - [[links]] from this note
    • Backlinks - notes that link to this note
    • Context - surrounding text for each link
    • Grouping - multiple links to same target
    • Link analysis - strength, frequency, context
    
    RETURNS:
    {
        "outlinks": [
            {"target": "Note B", "context": "discussing [[Note B]] benefits", "line": 15},
            {"target": "Note C", "context": "see also [[Note C]]", "line": 23}
        ],
        "backlinks": [
            {"source": "Note D", "context": "related to [[Current Note]]", "line": 8}
        ],
        "total_connections": 3,
        "connection_strength": "medium"
    }
    """
```

### 3. ✏️ `update_link` - Изменение связей
```python
@mcp.tool()
def update_link(
    ctx: Context[ServerSession, AppContext],
    from_note: str,
    old_target: str,
    new_target: str,
    update_all: bool = False,
    add_context: Optional[str] = None
) -> Dict[str, Any]:
    """
    ✏️ UPDATE LINK - Modify existing wikilinks
    
    PURPOSE: Change link targets or add context without manual editing
    
    FEATURES:
    • Rename link target: [[Old]] → [[New]]
    • Add context: [[Note]] → [[Note|with context]]
    • Bulk update: all instances in note
    • Validation: ensure new target exists
    • Preview: show what will change
    
    USE CASES:
    • Renaming: update_link("Project", "Old Name", "New Name")
    • Context: add descriptive text to links
    • Refactoring: mass rename across notes
    """
```

### 4. 🔍 `analyze_links` - Анализ связей
```python
@mcp.tool()  
def analyze_links(
    ctx: Context[ServerSession, AppContext],
    note_title: str,
    analysis_type: str = "full",  # "broken", "orphaned", "clusters"
    suggest_fixes: bool = True
) -> Dict[str, Any]:
    """
    🔍 ANALYZE LINKS - Health check for note connections
    
    PURPOSE: Find and fix link issues for healthy knowledge graph
    
    FEATURES:
    • Broken links - [[Non-existent Notes]]
    • Orphaned notes - no incoming connections
    • Link clusters - highly connected areas
    • Suggestions - recommended connections
    • Health score - overall link quality
    
    USE CASES:
    • Maintenance: find broken links to fix
    • Discovery: suggest related notes to connect
    • Optimization: identify over/under-connected notes
    """
```

## 🛠️ Implementation Plan

### Phase 2.1.1: Core Link Tools (2-3 дня)
1. **delete_link** - высший приоритет
2. **list_links** - для visibility
3. **Enhanced create_link** - улучшения текущего

### Phase 2.1.2: Advanced Link Tools (2-3 дня)  
4. **update_link** - для refactoring
5. **analyze_links** - для maintenance
6. **batch_link_operations** - для mass changes

## 📊 Expected Impact

### ✅ For AI/Users:
- **Symmetrical API** - create/delete/update/list
- **No manual editing** required for link management
- **Cognitive load reduction** - simple tool calls
- **Error reduction** - no manual text parsing

### ✅ For Knowledge Graph:
- **Cleaner connections** - easy removal of outdated links
- **Better maintenance** - analyze_links finds issues
- **Flexible refactoring** - mass updates possible
- **Health monitoring** - link quality metrics

## 🎯 Success Criteria
- [ ] delete_link removes specific [[wikilinks]] correctly
- [ ] Bidirectional deletion works both ways  
- [ ] Text formatting preserved during link removal
- [ ] list_links shows comprehensive connection view
- [ ] No manual content editing needed for link management
