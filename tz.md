# Telegram-бот проверки данных (zachestnyibiznes.ru)

## Описание задачи

Разработка Telegram-бота для проверки юридических и физических лиц по открытым государственным базам данных. Бот работает как розничная витрина поверх API сервиса zachestnyibiznes.ru. Целевая аудитория: работодатели, службы безопасности, юристы, HR.

Заказчик - самозанятый, покупает годовой доступ к API, перепродаёт проверки в розницу через бота.

Текущий этап: разработка каркаса бота со всей логикой, кроме интеграции с API zachestnyibiznes (будет доступен в марте) и подключения ЮKassa (подключается после получения реквизитов от заказчика).

## Требования

### Функционал пользователя

1. `/start` - регистрация, приветственное сообщение с описанием возможностей бота
2. `/help` - справка по командам и типам проверок
3. `/balance` - текущий баланс и история последних 10 операций
4. `/check_ul` - проверка юридического лица (по ИНН, ОГРН или названию)
5. `/check_fl` - проверка физического лица (по ФИО + дата рождения, или по паспортным данным)
6. `/check_ip` - проверка индивидуального предпринимателя (по ИНН или ОГРНИП)
7. `/topup` - пополнение баланса (генерация ссылки на оплату)
8. `/history` - история проверок с возможностью повторного просмотра результатов
9. `/prices` - список типов проверок и их стоимость

### Функционал администратора

10. `/admin_stats` - статистика: количество пользователей, проверок за день/неделю/месяц, сумма пополнений
11. `/admin_balance <tg_id> <сумма>` - ручное пополнение баланса пользователя (для приёма оплаты переводом на карту)
12. `/admin_users` - список пользователей с балансами
13. `/admin_broadcast <текст>` - рассылка сообщения всем пользователям

### Система баланса

14. Внутренний баланс в рублях
15. Списание ДО запроса к API
16. Автоматический возврат при ошибке API
17. Логирование всех транзакций (пополнение, списание, возврат)
18. Минимальная сумма пополнения - настраивается в конфиге

### Заглушки для будущей интеграции

19. Модуль API zachestnyibiznes - абстрактный класс/интерфейс с методами `check_ul()`, `check_fl()`, `check_ip()`. Сейчас возвращает моковые данные, потом подменяется реальным API
20. Модуль оплаты ЮKassa - абстрактный класс с методами `create_payment()`, `handle_webhook()`. Сейчас заглушка, подключается позже
21. Webhook-эндпоинт для ЮKassa (на aiohttp/fastapi) - готовый роут, ждёт подключения

## Технический стек

- **Python 3.12**
- **aiogram 3.x** - Telegram Bot API
- **SQLite** (через aiosqlite) - хранение данных. Для 1 ядра + 1 ГБ RAM оптимально, миграция на PostgreSQL при необходимости
- **aiohttp** - webhook-сервер для ЮKassa
- **pydantic** - валидация данных и конфигурация
- **Docker** - деплой (опционально)

## Архитектура

```
bot/
├── main.py              # Точка входа, запуск бота и webhook-сервера
├── config.py            # Настройки из .env (токен бота, цены, admin_ids)
├── handlers/
│   ├── user.py          # Хэндлеры пользовательских команд
│   ├── admin.py         # Хэндлеры админских команд
│   └── payment.py       # Хэндлеры пополнения и webhook ЮKassa
├── services/
│   ├── api_client.py    # Интерфейс + заглушка API zachestnyibiznes
│   ├── payment.py       # Интерфейс + заглушка ЮKassa
│   └── billing.py       # Логика баланса, списания, возвратов
├── database/
│   ├── db.py            # Подключение и инициализация БД
│   ├── models.py        # SQL-схемы таблиц
│   └── queries.py       # CRUD-операции
├── utils/
│   ├── formatters.py    # Форматирование ответов для Telegram
│   └── keyboards.py     # Inline-клавиатуры
├── .env.example         # Шаблон переменных окружения
├── requirements.txt
├── Makefile
└── README.md
```

### Схема БД

```sql
CREATE TABLE users (
    tg_id INTEGER PRIMARY KEY,
    username TEXT,
    full_name TEXT,
    balance REAL DEFAULT 0,
    is_admin INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id INTEGER REFERENCES users(tg_id),
    amount REAL,
    type TEXT CHECK(type IN ('topup', 'check', 'refund')),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id INTEGER REFERENCES users(tg_id),
    check_type TEXT CHECK(check_type IN ('ul', 'fl', 'ip')),
    query TEXT,
    result TEXT,
    cost REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id INTEGER REFERENCES users(tg_id),
    amount REAL,
    payment_id TEXT,
    status TEXT CHECK(status IN ('pending', 'succeeded', 'canceled')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Конфигурация (.env)

```
BOT_TOKEN=
ADMIN_IDS=123456,789012
CHECK_PRICE_UL=30
CHECK_PRICE_FL=50
CHECK_PRICE_IP=30
MIN_TOPUP=100
YOOKASSA_SHOP_ID=
YOOKASSA_SECRET_KEY=
ZACHESTNY_API_KEY=
WEBHOOK_HOST=
WEBHOOK_PORT=8080
```

## Входные данные от заказчика

- Telegram Bot Token (от BotFather)
- API-ключ zachestnyibiznes.ru (будет в марте)
- Реквизиты ЮKassa (shop_id, secret_key)
- Желаемые цены за проверки
- Список tg_id администраторов
- Сервер для деплоя (1 ядро, 1 ГБ RAM)

## Результат

Заказчик получает:
1. Работающий Telegram-бот с системой баланса и админкой
2. Моковые данные для демонстрации (заглушки API возвращают примеры реальных ответов)
3. Подробный README с инструкцией по деплою и подключению API/ЮKassa
4. Makefile для установки и запуска

Для запуска в продакшн заказчику останется:
- Вписать API-ключ zachestnyibiznes в .env
- Вписать реквизиты ЮKassa в .env
- Запустить `make all`

## Открытые вопросы

1. Какие именно типы проверок нужны на старте (ЮЛ, ФЛ, ИП - все три или часть)?
2. Какие цены за каждый тип проверки?
3. Нужна ли проверка паспорта как отдельный тип?
4. Нужно ли ограничение по количеству проверок в день на пользователя?
5. Нужна ли реферальная система или промокоды?
6. Формат вывода результатов - текст в сообщении, или генерация PDF?
