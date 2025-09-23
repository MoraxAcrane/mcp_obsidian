# 📥 Руководство по установке Enhanced Obsidian MCP Server

**Простая пошаговая инструкция для быстрого запуска MCP сервера**

---

## 🚀 Быстрая установка (рекомендуется)

### 1. Склонируйте репозиторий
```bash
git clone https://github.com/your-username/obsidian-mcp-server.git
cd obsidian-mcp-server
```

### 2. Запустите интерактивную установку
```bash
python setup.py
```

**Скрипт автоматически:**
- ✅ Проверит системные требования
- ✅ Установит все зависимости  
- ✅ Поможет настроить путь к Obsidian Vault
- ✅ Создаст конфигурационный файл
- ✅ Протестирует работоспособность
- ✅ Выдаст готовые JSON для вставки в ИИ-ассистентов

### 3. Скопируйте конфигурацию в ваш ИИ-ассистент

Скрипт выдаст готовые JSON конфигурации для:
- **Cursor IDE** → `.cursor/mcp.json`
- **Claude Desktop** → `claude_desktop_config.json`

---

## 🛠️ Ручная установка

### 1. Требования
- **Python 3.8+** 
- **Git**
- **Obsidian Vault** (папка с .md заметками)

### 2. Установка зависимостей
```bash
pip install -e .
```

### 3. Создание конфигурации
Создайте `obsidian_mcp_config.yaml`:
```yaml
vault:
  path: 'C:\path\to\your\Obsidian Vault'
```

### 4. Настройка ИИ-ассистентов

#### Cursor IDE
Файл: `.cursor/mcp.json`
```json
{
  "mcpServers": {
    "obsidian": {
      "command": "obsidian-ai-mcp",
      "args": ["--config", "obsidian_mcp_config.yaml"],
      "cwd": "/path/to/obsidian-mcp-server"
    }
  }
}
```

#### Claude Desktop  
Файл: `claude_desktop_config.json`
```json
{
  "mcpServers": {
    "obsidian": {
      "command": "obsidian-ai-mcp",
      "args": ["--config", "obsidian_mcp_config.yaml"],
      "cwd": "/path/to/obsidian-mcp-server"
    }
  }
}
```

---

## 🔍 Проверка установки

### Локальный тест
```bash
python start.py
```

### Прямая команда
```bash
obsidian-ai-mcp --config obsidian_mcp_config.yaml
```

### Как модуль Python
```bash
python -m obsidian_mcp.server --config obsidian_mcp_config.yaml
```

---

## ❓ Решение проблем

### Проблема: "obsidian-ai-mcp команда не найдена"
```bash
# Переустановите пакет
pip install -e . --force-reinstall

# Используйте альтернативный запуск
python -m obsidian_mcp.server --config obsidian_mcp_config.yaml
```

### Проблема: "Vault не найден"
1. Проверьте путь в `obsidian_mcp_config.yaml`
2. Убедитесь что путь содержит .md файлы или папку `.obsidian`
3. Используйте абсолютный путь без пробелов

### Проблема: "Модуль не найден"
```bash
# Убедитесь что находитесь в папке проекта
cd obsidian-mcp-server

# Переустановите зависимости
pip install -e .
```

### Проблема: "ИИ не видит MCP сервер"
1. Убедитесь что JSON скопирован правильно
2. Проверьте что пути в конфигурации корректны
3. Перезапустите Cursor IDE / Claude Desktop
4. Проверьте логи ИИ-ассистента

---

## 📂 Структура после установки

```
obsidian-mcp-server/
├── obsidian_mcp_config.yaml     ← Ваша конфигурация
├── setup.py                     ← Скрипт установки
├── start.py                     ← Простой запуск
├── src/obsidian_mcp/            ← Исходный код
├── tests/                       ← Тесты (опционально)
└── docs/                        ← Документация
```

---

## 🔐 Безопасность

✅ **Все данные остаются локально**  
✅ **Нет сетевых подключений**  
✅ **Работает только с вашим Obsidian Vault**  
✅ **Открытый исходный код**  

[Подробный анализ безопасности](MCP_SECURITY_ANALYSIS.md)

---

## 💡 Полезные команды

```bash
# Обновление до новой версии
git pull origin main
pip install -e . --force-reinstall

# Перезапуск конфигурации  
python setup.py

# Проверка статуса
python start.py

# Просмотр логов
python -m obsidian_mcp.server --config obsidian_mcp_config.yaml --verbose
```

---

## 🆘 Получить помощь

1. **GitHub Issues**: [Создать issue](https://github.com/your-username/obsidian-mcp-server/issues)
2. **Документация**: [README.md](README.md)
3. **Примеры**: [tests/](tests/) папка с тестами

---

**🎉 Готово! Наслаждайтесь умным MCP сервером для Obsidian!**
