@echo off
REM Быстрый тест MCP сервера
title MCP Server Tests
echo ========================================
echo    Тестирование MCP Сервера
echo ========================================
echo.
echo 📋 Выберите тест:
echo 1. Тест обычного сервера (obsidian-ai-mcp)
echo 2. Тест простого сервера (simple_server.py)
echo 3. Запустить оба теста
echo.
set /p choice="Введите номер (1-3): "

if "%choice%"=="1" (
    echo.
    echo 🧪 Тестирую обычный MCP сервер...
    python test_regular_client.py
) else if "%choice%"=="2" (
    echo.
    echo 🧪 Тестирую простой MCP сервер...
    python test_simple_client.py
) else if "%choice%"=="3" (
    echo.
    echo 🧪 Тестирую оба сервера...
    echo.
    echo === ТЕСТ ОБЫЧНОГО СЕРВЕРА ===
    python test_regular_client.py
    echo.
    echo === ТЕСТ ПРОСТОГО СЕРВЕРА ===
    python test_simple_client.py
) else (
    echo ❌ Неверный выбор!
)

pause
