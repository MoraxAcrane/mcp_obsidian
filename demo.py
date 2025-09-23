#!/usr/bin/env python3
"""
🎬 Enhanced Obsidian MCP Server - Демонстрация

Простая демонстрация возможностей MCP сервера для новых пользователей.
Показывает основные функции: создание заметок, поиск, чтение.
"""

import asyncio
import sys
import json
from pathlib import Path

# Попытка импорта MCP клиента для демо
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    print("❌ MCP библиотеки не установлены. Запустите: pip install -e .")
    sys.exit(1)

async def demo_mcp_server():
    """Демонстрация основных возможностей MCP сервера"""
    
    print("🎬 ДЕМОНСТРАЦИЯ ENHANCED OBSIDIAN MCP SERVER")
    print("=" * 60)
    
    # Проверяем конфигурацию
    config_file = Path("obsidian_mcp_config.yaml")
    if not config_file.exists():
        print("❌ Файл конфигурации не найден!")
        print("💡 Запустите сначала: python setup.py")
        return
    
    print("✅ Конфигурация найдена")
    print("🔄 Запускаем MCP сервер...")
    
    try:
        # Параметры для запуска сервера
        server_params = StdioServerParameters(
            command="python",
            args=["-m", "obsidian_mcp.server", "--config", str(config_file)]
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                
                # Инициализация
                await session.initialize()
                print("✅ MCP сервер подключен!")
                
                # Демо 1: Список заметок
                print("\n📋 ДЕМО 1: Получение списка заметок")
                print("-" * 40)
                
                result = await session.call_tool("list_notes", {"limit": 5})
                if result.content:
                    content = json.loads(result.content[0].text)
                    print(f"📊 Найдено заметок: {content.get('count', 0)}")
                    for note in content.get('notes', [])[:3]:
                        print(f"  📝 {note['title']} ({note.get('modified', 'дата неизвестна')})")
                else:
                    print("❌ Не удалось получить список заметок")
                
                # Демо 2: Создание тестовой заметки
                print("\n✏️ ДЕМО 2: Создание тестовой заметки")
                print("-" * 40)
                
                test_note_title = "MCP Demo Note"
                test_content = """# Демо заметка MCP сервера

Это тестовая заметка, созданная Enhanced Obsidian MCP Server!

## Возможности сервера:
- ✅ Создание и редактирование заметок
- 🔍 Умный поиск с многоязычной поддержкой  
- 🔗 Создание связей между заметками
- 🤖 Интеграция с ИИ-ассистентами

## Теги
#demo #mcp-server #obsidian

*Создано автоматически демо-скриптом*
"""
                
                try:
                    result = await session.call_tool("create_note", {
                        "title": test_note_title,
                        "content": test_content
                    })
                    print(f"✅ Создана заметка: {test_note_title}")
                except Exception as e:
                    print(f"⚠️ Заметка уже существует или ошибка: {e}")
                
                # Демо 3: Чтение заметки
                print("\n📖 ДЕМО 3: Чтение заметки")
                print("-" * 40)
                
                try:
                    result = await session.call_tool("read_note", {
                        "title": test_note_title,
                        "include_backlinks": True
                    })
                    if result.content:
                        content = json.loads(result.content[0].text)
                        print(f"📝 Заметка: {content['title']}")
                        print(f"📏 Длина: {len(content['content'])} символов")
                        print(f"🔗 Исходящие ссылки: {len(content.get('outlinks', []))}")
                        print(f"🔙 Входящие ссылки: {len(content.get('backlinks', []))}")
                except Exception as e:
                    print(f"❌ Ошибка при чтении заметки: {e}")
                
                # Демо 4: Умный поиск (если доступен)
                print("\n🔍 ДЕМО 4: Умный поиск")
                print("-" * 40)
                
                try:
                    result = await session.call_tool("explore_notes", {
                        "keywords": "demo mcp",
                        "limit": 3
                    })
                    if result.content:
                        content = json.loads(result.content[0].text)
                        print(f"🎯 Найдено заметок: {content.get('total_found', 0)}")
                        for note in content.get('results', [])[:2]:
                            relevance = note.get('relevance', 0)
                            print(f"  📝 {note['title']} (релевантность: {relevance:.1f})")
                    else:
                        print("❌ Умный поиск недоступен")
                except Exception as e:
                    print(f"⚠️ Explore_notes недоступен: {e}")
                    
                    # Fallback на обычный список
                    try:
                        result = await session.call_tool("list_notes", {"limit": 3})
                        print("✅ Используем обычный список заметок вместо поиска")
                    except:
                        pass
                
                print("\n" + "=" * 60)
                print("🎉 ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА!")
                print("=" * 60)
                
                print("\n📋 ЧТО ВЫ ВИДЕЛИ:")
                print("✅ Подключение к MCP серверу")
                print("✅ Получение списка заметок")
                print("✅ Создание новой заметки") 
                print("✅ Чтение заметки с метаданными")
                print("✅ Умный поиск (если доступен)")
                
                print("\n🎯 СЛЕДУЮЩИЕ ШАГИ:")
                print("1. Интегрируйте с Cursor IDE или Claude Desktop")
                print("2. Используйте конфигурацию из setup.py")
                print("3. Наслаждайтесь умной работой с заметками!")
                
                print(f"\n📁 Тестовая заметка создана: {test_note_title}")
                print("💡 Найдите её в своем Obsidian Vault")
    
    except Exception as e:
        print(f"❌ Ошибка при демонстрации: {e}")
        print("\n💡 ВОЗМОЖНЫЕ ПРИЧИНЫ:")
        print("1. MCP сервер не установлен: python setup.py")
        print("2. Неправильная конфигурация: проверьте obsidian_mcp_config.yaml")
        print("3. Obsidian Vault недоступен: проверьте путь в конфигурации")

def main():
    """Главная функция демо"""
    try:
        asyncio.run(demo_mcp_server())
    except KeyboardInterrupt:
        print("\n⏹️ Демонстрация прервана пользователем")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")

if __name__ == "__main__":
    main()
