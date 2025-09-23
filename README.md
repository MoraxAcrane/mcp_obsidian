# Obsidian AI MCP Server ✨

An advanced MCP (Model Context Protocol) server that provides **AI-optimized tools** for intelligent knowledge management in Obsidian vaults. Features both basic CRUD operations and enhanced AI-powered capabilities.

## 🆕 **Enhanced Version Available!**
- **12+ tools** including 6 new AI-optimized instruments  
- **Rich metadata** and analytics for better AI understanding
- **Smart creation** with auto-tagging and connection suggestions
- **Vault health analysis** and recommendations
- **Detailed AI usage guides** and system prompts

## Install

```bash
pip install -e .
```

## Configure

Create `obsidian_mcp_config.yaml` in your project root (or set `OBSIDIAN_MCP_CONFIG` env var).

```yaml
vault:
  path: "C:/path/to/your/ObsidianVault"
  templates_folder: "Templates"
  daily_notes_folder: "Daily Notes"
  attachments_folder: "Attachments"
```

If omitted, the server falls back to `./vault` (auto-created) or `OBSIDIAN_VAULT_PATH`.

## Run

- Stdio (default):
```bash
obsidian-ai-mcp
```

- SSE:
```bash
obsidian-ai-mcp --transport sse --port 8000
```

- Streamable HTTP:
```bash
obsidian-ai-mcp --transport streamable-http --port 8000
```

## 🛠️ Available Versions

### 🚀 **Enhanced Server** (Recommended)
```bash
start-enhanced.bat          # Windows - Enhanced version
python enhanced_run.py      # Cross-platform
```

**🆕 New AI-Optimized Tools:**
- `vault_overview` - comprehensive vault analytics & health metrics  
- `read_note_enhanced` - rich metadata (word count, links, structure, dates)
- `create_note_smart` - auto-tagging, folder suggestions, connection recommendations
- `note_exists` - existence check with similar note suggestions
- `append_to_note` - smart content addition with formatting & timestamps  
- `create_folder` - structured folder creation with index templates

### 📄 **Basic Server** (Compatible) 
```bash
start.bat                   # Windows - Basic version  
python simple_run.py        # Lightweight version
```

**Basic Tools:**
- `list_notes(folder?, limit?)` - list notes in vault
- `create_note(title, content, tags?, folder?)` - create new note
- `read_note(title, include_backlinks?, include_outlinks?)` - read note content
- `update_note(title, content?, append?, section?)` - update existing note  
- `delete_note(title)` - remove note
- `create_link(from_note, to_note, context?, bidirectional?)` - connect notes

## 💡 AI Integration (Cursor/Claude)

### Enhanced Server (Recommended):
```json
{
  "mcpServers": {
    "obsidian-enhanced-mcp": {
      "command": "python",
      "args": ["-c", "from obsidian_mcp.enhanced_server import main; import asyncio; asyncio.run(main())", "--config", "obsidian_mcp_config.yaml"],
      "type": "stdio",
      "cwd": "/path/to/mcp_obsidian"
    }
  }
}
```

### Basic Server (Compatible):
```json
{
  "mcpServers": {
    "obsidian-ai-mcp": {
      "command": "obsidian-ai-mcp", 
      "args": ["--config", "obsidian_mcp_config.yaml"],
      "type": "stdio"
    }
  }
}
```

### 🤖 For AI Developers:
See [`AI_USAGE_GUIDE.md`](AI_USAGE_GUIDE.md) for:
- System prompts optimized for AI understanding
- Detailed tool descriptions with use cases
- Workflow patterns and best practices
- Metrics and quality guidelines

## 🚀 Quick Start

### 1. Install & Test:
```bash
pip install -e .
python test_enhanced_client.py    # Test enhanced features
# OR
python test_regular_client.py     # Test basic features
```

### 2. Run Server:
```bash
# Enhanced (recommended)
start-enhanced.bat
# OR  
python enhanced_run.py

# Basic/Simple versions  
start.bat
start-simple.bat
```

### 3. Configuration:
```yaml
# obsidian_mcp_config.yaml
vault:
  path: "C:/path/to/your/ObsidianVault"
  templates_folder: "Templates"
  daily_notes_folder: "Daily Notes" 
  attachments_folder: "Attachments"
```

## 📚 Documentation

- [`AI_USAGE_GUIDE.md`](AI_USAGE_GUIDE.md) - System prompts & AI optimization
- [`enhancement_roadmap.md`](enhancement_roadmap.md) - Future development plans
- [`SOLUTION_LIGHTWEIGHT.md`](SOLUTION_LIGHTWEIGHT.md) - Troubleshooting guide
- [`FINAL_SOLUTION.md`](FINAL_SOLUTION.md) - Complete setup guide
