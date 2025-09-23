@echo off
REM Быстрый запуск MCP сервера Obsidian
title Obsidian MCP Server
echo ========================================
echo    Obsidian AI MCP Server
echo ========================================
echo.

REM Проверяем установку команды
obsidian-ai-mcp --help >nul 2>&1
if errorlevel 1 (
    echo ❌ Команда obsidian-ai-mcp не найдена!
    echo 💡 Запустите: pip install -e .
    pause
    exit /b 1
)

REM Запускаем сервер
echo 🚀 Запускаю MCP сервер в stdio режиме...
echo 📂 Конфигурация: %cd%\obsidian_mcp_config.yaml
echo ⚠️ Для остановки нажмите Ctrl+C
echo.
obsidian-ai-mcp --config obsidian_mcp_config.yaml
pause
