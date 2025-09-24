# 🧠 Enhanced Obsidian MCP Server

**AI-Powered Model Context Protocol Server для интеграции Obsidian с ИИ-ассистентами**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![MCP](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://github.com/modelcontextprotocol)

---

## ✨ Особенности

- 🔍 **Умный поиск** с многоязычной поддержкой (русский/английский)
- 🤖 **AI-оптимизированные инструменты** для работы с заметками
- ⚡ **Быстрая индексация** содержимого заметок
- 🔗 **Анализ связей** между заметками
- 🎯 **Контекстуальный поиск** с пониманием намерений
- 🛡️ **Безопасность** - все данные остаются локально

---

## 🚀 Простая установка за 2 минуты

### 🎯 Способ 1: Интерактивная установка (рекомендуется)
```bash
# 1. Склонируйте репозиторий
git clone https://github.com/your-username/obsidian-mcp-server.git
cd obsidian-mcp-server

# 2. Запустите мастер установки
python setup.py
```

**Скрипт автоматически:**
- ✅ Проверит системные требования
- ✅ Установит все зависимости
- ✅ Поможет найти ваш Obsidian Vault
- ✅ Создаст конфигурационный файл  
- ✅ Протестирует работоспособность
- ✅ **Выдаст готовый JSON для вставки в Cursor/Claude!**

### 🛠️ Способ 2: Ручная установка
```bash
# 1. Установка
git clone https://github.com/your-username/obsidian-mcp-server.git
cd obsidian-mcp-server
pip install -e .

# 2. Конфигурация
echo "vault:\n  path: 'C:\path\to\your\Obsidian Vault'" > obsidian_mcp_config.yaml

# 3. Запуск
python start.py
```

[📥 Подробная инструкция по установке](INSTALLATION_GUIDE.md)

---

## 🛠️ Доступные инструменты

### 📝 Базовые операции
- `list_notes` - Список последних заметок (с безопасными лимитами)
- `create_note` - Создание новой заметки
- `read_note` - Чтение заметки с метаданными
- `update_note` - Обновление содержимого заметки
- `delete_note` - Удаление заметки
- `create_link` - Создание связей между заметками

### 📁 Управление структурой
- `create_folder` - Создание папок (включая вложенные)
- `move_note` - Перемещение и переименование заметок
- `list_folders` - Обзор структуры папок с количеством заметок

### 🔍 Умный поиск
- `explore_notes` - Интеллектуальный поиск с:
  - Многоязычной поддержкой (русский ↔ английский)
  - Индексацией содержимого
  - Морфологическими вариантами
  - Оценкой релевантности
  - Превью содержимого

### 🤖 AI-оптимизация  
- `get_ai_usage_guide` - Полное руководство для ИИ-ассистентов:
  - Системный промпт с лучшими практиками
  - Примеры использования всех инструментов
  - Стратегии организации заметок
  - Рабочие процессы и шаблоны

---

## 🎯 Интеграция с ИИ-ассистентами

**💡 Конфигурации автоматически генерируются скриптом `setup.py`**

### Cursor IDE
Файл: `.cursor/mcp.json`
```json
{
  "mcpServers": {
    "obsidian": {
      "command": "obsidian-ai-mcp",
      "args": ["--config", "obsidian_mcp_config.yaml"],
      "cwd": "/path/to/your/project"
    }
  }
}
```

### Claude Desktop
Файл: `claude_desktop_config.json`  
```json
{
  "mcpServers": {
    "obsidian": {
      "command": "obsidian-ai-mcp",
      "args": ["--config", "obsidian_mcp_config.yaml"],
      "cwd": "/path/to/your/project"
    }
  }
}
```

> 🎯 **Скрипт `setup.py` автоматически сгенерирует правильные пути!**

---

## 📁 Структура проекта

```
obsidian-mcp-server/
├── src/obsidian_mcp/           # Основной код
│   ├── server.py               # MCP сервер
│   ├── smart_search.py         # Умный поиск
│   └── utils/                  # Вспомогательные утилиты
├── tests/                      # Тесты
├── start.py                    # Простой запускатель
├── obsidian_mcp_config.yaml    # Конфигурация
└── README.md                   # Документация
```

---

## 🔐 Безопасность

**Оценка безопасности: ВЫСОКАЯ** ✅

- ✅ **Локальные данные**: Все операции только в пределах Obsidian vault
- ✅ **Нет сетевых запросов**: Работает только локально
- ✅ **Изоляция путей**: Невозможен доступ к системным файлам
- ✅ **Безопасные лимиты**: Защита от перегрузки
- ✅ **Открытый код**: Весь исходный код доступен для аудита

[Подробный анализ безопасности](MCP_SECURITY_ANALYSIS.md)

---

## 📚 Документация

- [📥 Руководство по установке](INSTALLATION_GUIDE.md) - Подробная инструкция
- [🚀 Пример быстрого старта](QUICK_START_EXAMPLE.md) - Пошаговый пример
- [🎬 Демонстрация](demo.py) - Запустите `python demo.py`
- [Концепция проекта](obsidian_mcp_concept.md) - Архитектура и идеи
- [История проекта](PROJECT_CONTEXT_HISTORY.md) - Журнал изменений
- [План развития](PHASE_2_DETAILED_PLAN.md) - Следующие этапы
- [Анализ безопасности](MCP_SECURITY_ANALYSIS.md) - Детальная оценка

---

## 🤝 Участие в разработке

1. Форкните репозиторий
2. Создайте ветку для новой функции (`git checkout -b feature/amazing-feature`)
3. Зафиксируйте изменения (`git commit -m 'Add amazing feature'`)
4. Отправьте в ветку (`git push origin feature/amazing-feature`)
5. Создайте Pull Request

---

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. файл [LICENSE](LICENSE) для подробностей.

---

## 💡 Благодарности

- [Model Context Protocol](https://github.com/modelcontextprotocol) - Основа для интеграции
- [Obsidian](https://obsidian.md) - Платформа для управления знаниями
- [FastMCP](https://github.com/pydantic/fastmcp) - Быстрое создание MCP серверов

---

**🚀 Начните использовать Enhanced Obsidian MCP Server уже сегодня!**