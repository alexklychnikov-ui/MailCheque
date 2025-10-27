@echo off
echo ================================
echo   MailCheque - Сборка в .exe
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

REM Устанавливаем зависимости если нужно
echo Проверка зависимостей...
pip install pyinstaller >nul 2>&1

REM Запускаем сборку
echo Запуск сборки...
python build.py

echo.
echo ================================
echo   Сборка завершена
echo ================================
echo.
echo Исполняемый файл: dist\MailCheque.exe
echo Портативный пакет: MailCheque_Portable\
echo.
pause














