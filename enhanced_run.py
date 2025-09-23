#!/usr/bin/env python3
"""
Запуск улучшенного MCP сервера с расширенной функциональностью
"""

import os
import subprocess
import sys
from pathlib import Path


def run_enhanced_server():
    """Запуск расширенного MCP сервера"""
    print("🚀 Запускаю Enhanced MCP сервер с расширенной функциональностью...")
    print("✨ Новые возможности:")
    print("  • vault_overview - анализ здоровья vault")
    print("  • read_note_enhanced - расширенные метаданные")
    print("  • create_note_smart - умное создание с автотегами")
    print("  • append_to_note - умное добавление контента")
    print("  • note_exists - проверка существования")
    print("  • create_folder - структурирование vault")
    
    # Команда для запуска enhanced сервера
    cmd = [sys.executable, "-c", "from obsidian_mcp.enhanced_server import main; import asyncio; asyncio.run(main())"]
    
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
    
    print("=" * 60)
    print("📡 Enhanced MCP сервер запущен. Нажмите Ctrl+C для остановки.")
    print("🔧 Доступно 12+ инструментов включая новые enhanced версии")
    print("🤖 ИИ-оптимизированные описания для лучшего понимания")
    print("=" * 60)
    
    try:
        subprocess.run(cmd, env=env, check=True)
    except KeyboardInterrupt:
        print("\n✅ Enhanced сервер остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(run_enhanced_server())
