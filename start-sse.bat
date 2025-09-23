@echo off
REM Запуск MCP сервера в SSE режиме
title Obsidian MCP Server (SSE)
echo ========================================
echo    Obsidian AI MCP Server - SSE Mode
echo ========================================
echo.
echo 🚀 Запускаю MCP сервер в SSE режиме на порту 8000...
echo 🌐 URL: http://localhost:8000/sse
echo ⚠️ Для остановки нажмите Ctrl+C
echo.
obsidian-ai-mcp --transport sse --port 8000 --config obsidian_mcp_config.yaml
pause
