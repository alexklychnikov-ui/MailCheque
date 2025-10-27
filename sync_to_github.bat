@echo off
REM --- Настройте переменные перед запуском ---
SET REPO_URL=https://github.com/alexklychnikov-ui/https://github.com/alexklychnikov-ui/MailCheque.git

REM Инициализация git репозитория в текущей папке
git init

REM Добавление всех файлов
git add .

REM Первый коммит
git commit -m "Initial commit"

REM Добавление ссылки на удалённый репозиторий
git remote add origin %REPO_URL%

REM Отправка изменений в удалённый репозиторий
git push -u origin master

pause
