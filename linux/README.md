# Школьный бот для MAX

Бот показывает расписание, домашние задания и события. ИИ-помощник на GigaChat объясняет темы, составляет тесты и проверяет решения. В деморежиме уже есть пример расписания и заданий.

## Настройка

В `.env` уже настроены MAX и GigaChat.

## Сборка и запуск через Compose

Команды выполняются в папке проекта.

```sh
docker compose build
docker compose up -d
docker compose logs -f bot
```

База SQLite лежит в папке `data`. Остановка — `docker compose down`.

## Запуск готового образа

Архив `maxbot-linux-amd64.tar.gz` содержит образ `maxbot:beta` для Linux x86-64. Команды ниже загружают образ и запускают контейнер.

```sh
docker load -i maxbot-linux-amd64.tar.gz
docker run -d --name maxbot --env-file .env --env MAX_DB_PATH=/data/school_bot.db --mount type=volume,source=maxbot-data,target=/data maxbot:beta
docker logs -f maxbot
```

При таком запуске база хранится в томе `maxbot-data`. Остановка — `docker stop maxbot`. Достаточно выбрать один способ запуска, чтобы два экземпляра не работали с одним токеном MAX.

В `requirements.txt` указаны версии библиотек, нужных для запуска. Сборка использует Python 3.11.
