# 🚀 Быстрый старт Obsidian MCP Server

## Запуск одной командой

### Windows (проще всего)
```bash
# Дважды кликните по файлу или в командной строке:
start.bat          # Основной запуск (stdio режим)
start-sse.bat      # SSE режим для веб-доступа
test.bat           # Тестирование сервера
```

### Python (универсально)
```bash
python run.py                # Stdio режим (по умолчанию)
python run.py --sse          # SSE режим на порту 8000
python run.py --http         # HTTP режим на порту 8000
python run.py --test         # Запуск тестов
python run.py --port 9000    # Другой порт
```

### Прямой запуск
```bash
obsidian-ai-mcp              # После pip install -e .
```

## Конфигурация

Редактируйте `obsidian_mcp_config.yaml`:
```yaml
vault:
  path: 'C:\путь\к\вашему\Obsidian Vault'
  templates_folder: "Templates"
  daily_notes_folder: "Daily Notes"
  attachments_folder: "Attachments"
```

## Доступные инструменты MCP

1. **`list_notes`** - список заметок в vault
2. **`create_note`** - создание новой заметки  
3. **`read_note`** - чтение заметки с метаданными
4. **`update_note`** - обновление существующей заметки
5. **`delete_note`** - удаление заметки
6. **`create_link`** - создание связей между заметками

## Использование в Cursor/Claude

Добавьте в MCP конфигурацию:
```json
{
  "mcpServers": {
    "obsidian-ai-mcp": {
      "command": "obsidian-ai-mcp",
      "args": [],
      "type": "stdio"
    }
  }
}
```

## Статус проекта: ✅ Полностью функционален
- ✅ Все инструменты работают
- ✅ Проблемы с пустым содержимым решены  
- ✅ Тесты проходят успешно
- ✅ Удобный запуск настроен
