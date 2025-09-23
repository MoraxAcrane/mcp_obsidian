#!/usr/bin/env python3
"""
Удобный скрипт запуска MCP сервера Obsidian
Использование:
  python run.py              # stdio режим (по умолчанию)
  python run.py --sse         # SSE режим на порту 8000
  python run.py --http        # HTTP режим на порту 8000
  python run.py --port 9000   # Изменить порт
  python run.py --test        # Запустить тесты
"""

import argparse
import asyncio
import os
import subprocess
import sys
from pathlib import Path


def run_server(transport="stdio", port=8000):
    """Запускает MCP сервер"""
    
    # Пробуем сначала команду, затем прямой запуск
    config_file = Path("obsidian_mcp_config.yaml")
    
    # Вариант 1: Прямой запуск через Python модуль
    cmd = [sys.executable, "-m", "obsidian_mcp.server"]
    
    if transport != "stdio":
        cmd.extend(["--transport", transport])
        cmd.extend(["--port", str(port)])
    
    if config_file.exists():
        cmd.extend(["--config", str(config_file)])
        
    print(f"🚀 Запускаю MCP сервер: {' '.join(cmd)}")
    print(f"📂 Конфигурация: {'найдена' if config_file.exists() else 'используется по умолчанию'}")
    print("=" * 50)
    
    try:
        # Добавляем src в Python path
        env = os.environ.copy()
        src_path = str(Path(__file__).parent / "src")
        current_path = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = src_path + (os.pathsep + current_path if current_path else "")
        
        subprocess.run(cmd, check=True, env=env)
    except KeyboardInterrupt:
        print("\n✅ Сервер остановлен пользователем")
    except FileNotFoundError:
        print("❌ Ошибка: пакет obsidian_mcp не найден")
        print("💡 Попробуйте: pip install -e .")
        return 1
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка запуска сервера: {e}")
        return 1
    return 0


async def run_tests():
    """Запускает smoke тесты"""
    print("🧪 Запускаю тесты MCP сервера...")
    try:
        result = subprocess.run([sys.executable, "tests/smoke_client.py"], 
                              capture_output=True, text=True, check=False)
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print("✅ Тесты прошли успешно!")
        else:
            print(f"❌ Тесты завершились с ошибкой (код {result.returncode})")
        return result.returncode
    except Exception as e:
        print(f"❌ Ошибка запуска тестов: {e}")
        return 1


def main():
    parser = argparse.ArgumentParser(description="Obsidian MCP Server Launcher")
    
    # Режимы транспорта
    transport_group = parser.add_mutually_exclusive_group()
    transport_group.add_argument("--sse", action="store_true", 
                               help="Запустить в SSE режиме")
    transport_group.add_argument("--http", action="store_true", 
                               help="Запустить в HTTP режиме")
    
    parser.add_argument("--port", type=int, default=8000, 
                       help="Порт для SSE/HTTP (по умолчанию: 8000)")
    parser.add_argument("--test", action="store_true", 
                       help="Запустить тесты вместо сервера")
    
    args = parser.parse_args()
    
    if args.test:
        return asyncio.run(run_tests())
    
    # Определяем транспорт
    transport = "stdio"  # по умолчанию
    if args.sse:
        transport = "sse"
    elif args.http:
        transport = "streamable-http"
    
    return run_server(transport, args.port)


if __name__ == "__main__":
    sys.exit(main())
