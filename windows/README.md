# Запуск на Windows

Нужен Python 3.11 или новее. Откройте PowerShell в папке `windows` и подготовьте окружение.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Файл .env отправим отдельно.

Запустите `RUN_BOT.bat` или выполните команду.

```powershell
.\.venv\Scripts\python.exe -m maxbot
```

База создаётся в файле `school_bot.db`. Остановка — `Ctrl+C`.
