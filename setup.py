#!/usr/bin/env python3
"""
🚀 Enhanced Obsidian MCP Server - Интерактивная установка

Простая установка и настройка MCP сервера для работы с Obsidian и ИИ-ассистентами.
Запустите этот скрипт после клонирования репозитория с GitHub.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
import platform

def print_banner():
    """Красивый баннер приветствия"""
    print("\n" + "="*60)
    print("🧠 ENHANCED OBSIDIAN MCP SERVER")
    print("   Интерактивная установка и настройка")
    print("="*60 + "\n")

def print_step(step, description):
    """Форматированный вывод шага"""
    print(f"📋 Шаг {step}: {description}")
    print("-" * 50)

def print_success(message):
    """Успешное завершение"""
    print(f"✅ {message}")

def print_error(message):
    """Ошибка"""
    print(f"❌ {message}")

def print_warning(message):
    """Предупреждение"""
    print(f"⚠️ {message}")

def check_python_version():
    """Проверка версии Python"""
    print_step(1, "Проверка системных требований")
    
    if sys.version_info < (3, 8):
        print_error(f"Требуется Python 3.8 или новее. У вас: {sys.version}")
        print("📥 Скачайте Python: https://www.python.org/downloads/")
        return False
    
    print_success(f"Python {sys.version.split()[0]} ✓")
    print_success(f"Операционная система: {platform.system()} {platform.release()}")
    return True

def install_dependencies():
    """Установка зависимостей"""
    print_step(2, "Установка зависимостей")
    
    try:
        print("🔄 Устанавливаю пакет в режиме разработки...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-e", ".", "--quiet"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print_error("Ошибка при установке зависимостей:")
            print(result.stderr)
            return False
            
        print_success("Все зависимости установлены")
        return True
        
    except Exception as e:
        print_error(f"Не удалось установить зависимости: {e}")
        return False

def get_vault_path():
    """Интерактивный выбор пути к Obsidian Vault"""
    print_step(3, "Настройка пути к Obsidian Vault")
    
    print("📁 Укажите путь к вашему Obsidian Vault")
    print("💡 Это папка, где хранятся ваши .md заметки\n")
    
    # Предложить стандартные пути
    suggested_paths = []
    
    if platform.system() == "Windows":
        suggested_paths = [
            Path.home() / "Documents" / "Obsidian Vault",
            Path.home() / "OneDrive" / "Документы" / "Obsidian Vault",
            Path.home() / "OneDrive" / "Documents" / "Obsidian Vault",
        ]
    elif platform.system() == "Darwin":  # macOS
        suggested_paths = [
            Path.home() / "Documents" / "Obsidian Vault",
            Path.home() / "iCloud Drive (Archive)" / "Obsidian Vault",
        ]
    else:  # Linux
        suggested_paths = [
            Path.home() / "Documents" / "Obsidian Vault",
            Path.home() / "Obsidian Vault",
        ]
    
    # Проверить существующие пути
    existing_paths = [path for path in suggested_paths if path.exists()]
    
    if existing_paths:
        print("🔍 Найдены возможные Vault'ы:")
        for i, path in enumerate(existing_paths, 1):
            note_count = len(list(path.glob("**/*.md")))
            print(f"  {i}. {path} ({note_count} заметок)")
        print(f"  {len(existing_paths) + 1}. Указать другой путь")
        print()
        
        while True:
            try:
                choice = input(f"Выберите вариант (1-{len(existing_paths) + 1}): ").strip()
                if choice == str(len(existing_paths) + 1):
                    break
                elif 1 <= int(choice) <= len(existing_paths):
                    return str(existing_paths[int(choice) - 1])
            except (ValueError, IndexError):
                print_warning("Введите корректный номер")
    
    # Ручной ввод пути
    while True:
        vault_path = input("\n📂 Введите полный путь к Obsidian Vault: ").strip()
        
        if not vault_path:
            print_warning("Путь не может быть пустым")
            continue
        
        # Убираем кавычки если есть
        vault_path = vault_path.strip('"\'')
        path_obj = Path(vault_path)
        
        if not path_obj.exists():
            print_warning(f"Путь не существует: {vault_path}")
            create = input("Создать директорию? (y/n): ").lower().strip()
            if create in ['y', 'yes', 'да', 'д']:
                try:
                    path_obj.mkdir(parents=True, exist_ok=True)
                    print_success(f"Создана директория: {vault_path}")
                    return vault_path
                except Exception as e:
                    print_error(f"Не удалось создать директорию: {e}")
                    continue
            continue
        
        # Проверить что это похоже на Vault
        md_files = list(path_obj.glob("**/*.md"))
        obsidian_folder = path_obj / ".obsidian"
        
        if md_files or obsidian_folder.exists():
            print_success(f"Найдено {len(md_files)} заметок в Vault")
            return vault_path
        else:
            print_warning("В указанной папке нет .md файлов или .obsidian папки")
            proceed = input("Продолжить с этим путем? (y/n): ").lower().strip()
            if proceed in ['y', 'yes', 'да', 'д']:
                return vault_path

def create_config(vault_path):
    """Создание конфигурационного файла"""
    print_step(4, "Создание конфигурации")
    
    config = {
        'vault': {
            'path': vault_path
        },
        'server': {
            'name': 'enhanced-obsidian-mcp',
            'version': '1.0.0'
        },
        'search': {
            'index_content': True,
            'case_sensitive': False,
            'multilingual': True,
            'max_results': 20
        },
        'limits': {
            'max_notes_list': 50,
            'max_search_results': 30,
            'content_preview_chars': 300
        }
    }
    
    config_file = Path("obsidian_mcp_config.yaml")
    
    try:
        import yaml
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    except ImportError:
        # Fallback: создаем YAML вручную если PyYAML недоступен
        yaml_content = f"""# Конфигурация Enhanced Obsidian MCP Server
vault:
  path: '{vault_path}'

server:
  name: 'enhanced-obsidian-mcp'
  version: '1.0.0'

search:
  index_content: true
  case_sensitive: false
  multilingual: true
  max_results: 20

limits:
  max_notes_list: 50
  max_search_results: 30
  content_preview_chars: 300
"""
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
    
    print_success(f"Создан файл конфигурации: {config_file.absolute()}")
    return config_file

def test_server():
    """Тестирование работоспособности сервера"""
    print_step(5, "Тестирование MCP сервера")
    
    print("🔄 Проверяю работоспособность сервера...")
    
    try:
        # Проверяем что команда obsidian-ai-mcp доступна
        result = subprocess.run([
            "obsidian-ai-mcp", "--help"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print_success("Команда obsidian-ai-mcp работает")
            return True
        else:
            print_warning("Команда obsidian-ai-mcp недоступна, используем python модуль")
            # Тест через модуль
            result = subprocess.run([
                sys.executable, "-m", "obsidian_mcp.server", "--help"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print_success("Python модуль работает")
                return True
    
    except Exception as e:
        print_error(f"Ошибка при тестировании: {e}")
    
    return False

def generate_integration_configs(vault_path):
    """Генерация конфигураций для интеграции с ИИ"""
    print_step(6, "Генерация конфигураций для ИИ-ассистентов")
    
    current_dir = str(Path().absolute()).replace('\\', '/')
    
    # Конфигурация для Cursor IDE
    cursor_config = {
        "mcpServers": {
            "obsidian": {
                "command": "obsidian-ai-mcp",
                "args": ["--config", "obsidian_mcp_config.yaml"],
                "cwd": current_dir,
                "env": {}
            }
        }
    }
    
    # Альтернативная конфигурация через Python модуль
    cursor_config_alt = {
        "mcpServers": {
            "obsidian": {
                "command": "python",
                "args": ["-m", "obsidian_mcp.server", "--config", "obsidian_mcp_config.yaml"],
                "cwd": current_dir,
                "env": {}
            }
        }
    }
    
    # Конфигурация для Claude Desktop
    claude_config = {
        "mcpServers": {
            "obsidian": {
                "command": "obsidian-ai-mcp",
                "args": ["--config", "obsidian_mcp_config.yaml"],
                "cwd": current_dir
            }
        }
    }
    
    print("\n" + "="*60)
    print("📋 КОНФИГУРАЦИИ ДЛЯ ИИ-АССИСТЕНТОВ")
    print("="*60)
    
    print("\n🎯 ДЛЯ CURSOR IDE")
    print("📁 Файл: .cursor/mcp.json")
    print("📝 Скопируйте этот JSON:")
    print("-" * 40)
    print(json.dumps(cursor_config, indent=2, ensure_ascii=False))
    
    print("\n💡 Альтернативный вариант для Cursor (если первый не работает):")
    print("-" * 40)
    print(json.dumps(cursor_config_alt, indent=2, ensure_ascii=False))
    
    print("\n🤖 ДЛЯ CLAUDE DESKTOP")
    print("📁 Файл: claude_desktop_config.json")
    print("📝 Скопируйте этот JSON:")
    print("-" * 40)
    print(json.dumps(claude_config, indent=2, ensure_ascii=False))
    
    print("\n" + "="*60)

def main():
    """Основная функция установки"""
    print_banner()
    
    try:
        # Шаг 1: Проверка Python
        if not check_python_version():
            return 1
        
        # Шаг 2: Установка зависимостей
        if not install_dependencies():
            return 1
        
        # Шаг 3: Получение пути к Vault
        vault_path = get_vault_path()
        if not vault_path:
            return 1
        
        # Шаг 4: Создание конфигурации
        config_file = create_config(vault_path)
        
        # Шаг 5: Тестирование
        if not test_server():
            print_warning("Сервер не прошел тест, но возможно все равно будет работать")
        
        # Шаг 6: Генерация конфигураций
        generate_integration_configs(vault_path)
        
        # Финальные инструкции
        print("\n" + "="*60)
        print("🎉 УСТАНОВКА ЗАВЕРШЕНА УСПЕШНО!")
        print("="*60)
        
        print("\n📋 КАК ЗАПУСТИТЬ:")
        print("1. Локально:           python start.py")
        print("2. Прямая команда:     obsidian-ai-mcp")
        print("3. Как модуль:         python -m obsidian_mcp.server")
        
        print("\n🔧 ИНТЕГРАЦИЯ С ИИ:")
        print("1. Скопируйте JSON выше в настройки вашего ИИ-ассистента")
        print("2. Перезапустите Cursor IDE или Claude Desktop")
        print("3. MCP сервер должен появиться в списке доступных инструментов")
        
        print("\n📚 ДОКУМЕНТАЦИЯ:")
        print("- README.md           - Полное руководство")
        print("- MCP_SECURITY_ANALYSIS.md - Анализ безопасности")
        print("- PHASE_2_DETAILED_PLAN.md - План развития")
        
        print(f"\n📁 VAULT: {vault_path}")
        print(f"⚙️ CONFIG: {Path('obsidian_mcp_config.yaml').absolute()}")
        
        print("\n🚀 ГОТОВО К ИСПОЛЬЗОВАНИЮ!")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Установка прервана пользователем")
        return 130
    
    except Exception as e:
        print_error(f"Неожиданная ошибка: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
