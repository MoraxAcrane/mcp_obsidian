#!/usr/bin/env python3
"""
Простой запуск MCP сервера без лишних зависимостей
"""

import os
import subprocess
import sys
from pathlib import Path


def run_simple_server():
    """Запуск упрощенного сервера"""
    print("🚀 Запускаю простой MCP сервер (минимальные зависимости)...")
    print("📦 Зависимости: mcp, PyYAML, python-frontmatter")
    print("🎯 Без torch, transformers, spacy, nltk - быстрый запуск!")
    
    # Команда для запуска простого сервера
    cmd = [sys.executable, "-c", "from obsidian_mcp.simple_server import main; import asyncio; asyncio.run(main())"]
    
    # Добавляем конфиг если есть
    config_file = Path("obsidian_mcp_config.yaml")
    if config_file.exists():
        cmd.extend(["--config", str(config_file)])
        print(f"📂 Конфигурация: {config_file}")
        
        # Показываем путь к vault
        try:
            import yaml
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
                vault_path = config_data.get('vault', {}).get('path', 'не указан')
                print(f"🗂️ Vault: {vault_path}")
        except:
            pass
    else:
        print("📂 Конфигурация: по умолчанию (./vault)")
    
    # Настройка окружения
    env = os.environ.copy()
    src_path = str(Path(__file__).parent / "src")
    current_path = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = src_path + (os.pathsep + current_path if current_path else "")
    
    print("=" * 50)
    print("📡 MCP сервер запущен. Нажмите Ctrl+C для остановки.")
    print("🔧 Доступно 6 инструментов: list_notes, create_note, read_note, update_note, delete_note, create_link")
    print("=" * 50)
    
    try:
        subprocess.run(cmd, env=env, check=True)
    except KeyboardInterrupt:
        print("\n✅ Сервер остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(run_simple_server())
