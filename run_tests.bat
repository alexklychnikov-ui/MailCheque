@echo off
echo ================================
echo   MailCheque - Запуск тестов
echo ================================
echo.

REM Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Ошибка: Python не найден в PATH
    echo Установите Python 3.7+ и добавьте в PATH
    pause
    exit /b 1
)

echo Python найден
echo.

REM Запускаем тесты
echo Запуск всех тестов...
python tests/run_tests.py

echo.
echo ================================
echo   Тесты завершены
echo ================================
pause














