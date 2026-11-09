# Запуск на Windows

Нужен Python 3.11 или новее. Откройте PowerShell в папке `windows` и подготовьте окружение.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Мы собрали все файлы. Если GigaChat не работает - недоброжелатели потратили все преобритённые токены.

При самостоятельной настройке скопируйте `.env.example` в `.env`, заполните `MAX_BOT_TOKEN` и при необходимости `GIGACHAT_AUTH_KEY`. Удалите из `.env` строки с незаполненными параметрами, чтобы бот использовал значения по умолчанию.

Запустите `RUN_BOT.bat` или выполните команду.

```powershell
.\.venv\Scripts\python.exe -m maxbot
```

База создаётся в файле `school_bot.db`. Остановка — `Ctrl+C`.
