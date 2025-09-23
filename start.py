#!/usr/bin/env python3
"""
🚀 Enhanced Obsidian MCP Server - Quick Start

Простой запускатель для MCP сервера Obsidian с AI поддержкой.
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Запуск Enhanced Obsidian MCP Server"""
    
    # Проверка конфигурации
    config_file = Path("obsidian_mcp_config.yaml")
    if not config_file.exists():
        print("❌ Конфигурационный файл не найден!")
        print("📝 Создайте файл obsidian_mcp_config.yaml с содержимым:")
        print("""
vault:
  path: 'C:\\path\\to\\your\\Obsidian Vault'
""")
        return 1
    
    print("🚀 Запуск Enhanced Obsidian MCP Server...")
    print("📁 Конфигурация: obsidian_mcp_config.yaml")
    print("💡 Режим: stdio (совместим с Cursor IDE)")
    print("⚡ Функции: Умный поиск + AI анализ + Быстрое создание заметок")
    print("")
    print("🔄 Запуск сервера...")
    
    try:
        # Запуск основного MCP сервера
        result = subprocess.run([
            sys.executable, "-m", "obsidian_mcp.server",
            "--config", str(config_file)
        ], cwd=Path(__file__).parent)
        
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n⏹️  Сервер остановлен пользователем")
        return 0
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        print("💡 Попробуйте: obsidian-ai-mcp --config obsidian_mcp_config.yaml")
        return 1

if __name__ == "__main__":
    exit(main())
