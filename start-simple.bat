@echo off
REM Запуск простого MCP сервера без тяжелых зависимостей
title Simple Obsidian MCP Server
echo ===============================================
echo    Simple Obsidian MCP Server (Lightweight)
echo ===============================================
echo.
echo 🚀 Запускаю упрощенный MCP сервер...
echo 📦 Без тяжелых зависимостей (torch, transformers, etc)
echo 📂 Vault: %cd%\obsidian_mcp_config.yaml
echo.
echo ⚠️ Для остановки нажмите Ctrl+C
echo.
python simple_run.py
pause
