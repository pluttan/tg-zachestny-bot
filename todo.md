# TODO: Telegram-бот проверки данных (zachestnyibiznes.ru)

## Подготовка

- [ ] Создать структуру проекта согласно архитектуре из tz.md
- [ ] Инициализировать git, .gitignore (исключить .env, __pycache__, *.db, venv/)
- [ ] Создать Makefile (install, run, all)
- [ ] Создать requirements.txt: aiogram>=3.0, aiosqlite, aiohttp, pydantic, pydantic-settings, python-dotenv
- [ ] Создать .env.example со всеми переменными
- [ ] Создать config.py на pydantic-settings: загрузка BOT_TOKEN, ADMIN_IDS, цены проверок, настройки ЮKassa, настройки webhook

## База данных

- [ ] database/db.py - async подключение к SQLite через aiosqlite, инициализация таблиц при старте
- [ ] database/models.py - SQL-запросы создания таблиц: users, transactions, checks, payments
- [ ] database/queries.py - CRUD-функции:
  - `get_or_create_user(tg_id, username, full_name)`
  - `get_balance(tg_id) -> float`
  - `add_transaction(tg_id, amount, type, description)`
  - `deduct_balance(tg_id, amount, description) -> bool`
  - `refund_balance(tg_id, amount, description)`
  - `topup_balance(tg_id, amount, description)`
  - `save_check(tg_id, check_type, query, result, cost)`
  - `get_checks_history(tg_id, limit=10)`
  - `get_transactions_history(tg_id, limit=10)`
  - `get_all_users()`
  - `get_stats(period)` - количество пользователей, проверок, сумма пополнений за период
  - `get_all_tg_ids()` - для рассылки

## Сервисы

- [ ] services/api_client.py - абстрактный класс `BaseAPIClient` с методами:
  - `async check_ul(query: str) -> dict` - проверка юрлица
  - `async check_fl(query: str) -> dict` - проверка физлица
  - `async check_ip(query: str) -> dict` - проверка ИП
  - Реализация `MockAPIClient` - возвращает правдоподобные моковые данные (пример выписки ЕГРЮЛ, данные ФЛ из открытых баз). Моки должны быть реалистичными чтобы заказчик мог демонстрировать бота
  - Реализация `ZachestnyAPIClient` - заглушка с TODO, куда потом вписывается реальный код. Конструктор принимает api_key, base_url

- [ ] services/payment.py - абстрактный класс `BasePaymentProvider` с методами:
  - `async create_payment(amount: float, description: str, tg_id: int) -> str` - возвращает URL оплаты
  - `async handle_webhook(data: dict) -> tuple[int, float]` - возвращает (tg_id, amount)
  - Реализация `MockPaymentProvider` - create_payment возвращает заглушку "Оплата временно недоступна, обратитесь к администратору", handle_webhook - заглушка
  - Реализация `YooKassaProvider` - заглушка с TODO

- [ ] services/billing.py - логика биллинга:
  - `async process_check(tg_id, check_type, query)` - проверка баланса, списание, вызов API, сохранение результата, возврат при ошибке
  - `async process_topup(tg_id, amount)` - создание платежа через PaymentProvider
  - `async confirm_topup(tg_id, amount)` - начисление баланса после подтверждения оплаты
  - Цены проверок берутся из config.py

## Хэндлеры пользователя

- [ ] handlers/user.py:
  - `/start` - регистрация пользователя в БД, приветственное сообщение с inline-клавиатурой (Проверить ЮЛ, Проверить ФЛ, Проверить ИП, Баланс, Помощь)
  - `/help` - описание всех команд и типов проверок
  - `/balance` - показать баланс + последние 5 транзакций
  - `/prices` - таблица цен
  - `/history` - последние 10 проверок, каждая как inline-кнопка для повторного просмотра
  - `/check_ul` - запрос ИНН/ОГРН/названия, вызов billing.process_check('ul', query)
  - `/check_fl` - запрос ФИО + доп. данных, вызов billing.process_check('fl', query)
  - `/check_ip` - запрос ИНН/ОГРНИП, вызов billing.process_check('ip', query)
  - `/topup` - выбор суммы (inline-кнопки: 100, 300, 500, 1000 руб или ввод вручную), генерация ссылки на оплату
  - Для проверок использовать FSM (aiogram states): ожидание ввода запроса после команды

## Хэндлеры администратора

- [ ] handlers/admin.py (проверка tg_id в ADMIN_IDS):
  - `/admin_stats` - количество пользователей, проверок и сумма пополнений за сегодня / неделю / месяц
  - `/admin_balance <tg_id> <сумма>` - ручное начисление баланса + уведомление пользователю
  - `/admin_users` - список пользователей (tg_id, username, баланс, дата регистрации), пагинация если >20
  - `/admin_broadcast` - запрос текста через FSM, подтверждение, рассылка всем пользователям

## Хэндлеры оплаты

- [ ] handlers/payment.py:
  - Webhook-роут POST /payment/webhook - приём уведомлений от ЮKassa
  - Верификация подписи (заглушка)
  - Вызов billing.confirm_topup при успешной оплате
  - Уведомление пользователя о зачислении

## Утилиты

- [ ] utils/keyboards.py - inline-клавиатуры:
  - Главное меню (после /start)
  - Выбор суммы пополнения
  - Подтверждение проверки ("Проверить за X руб?")
  - Навигация по истории
  - Админ-меню

- [ ] utils/formatters.py - форматирование ответов:
  - `format_ul_result(data: dict) -> str` - красивый вывод данных юрлица (название, ИНН, ОГРН, статус, руководитель, адрес и т.д.)
  - `format_fl_result(data: dict) -> str` - вывод данных физлица
  - `format_ip_result(data: dict) -> str` - вывод данных ИП
  - `format_balance(balance, transactions) -> str`
  - `format_stats(stats) -> str`
  - Все форматтеры используют Telegram HTML-разметку

## Точка входа

- [ ] main.py:
  - Загрузка конфига
  - Инициализация БД
  - Инициализация сервисов (MockAPIClient или ZachestnyAPIClient в зависимости от наличия API-ключа)
  - Регистрация хэндлеров
  - Параллельный запуск: aiogram polling + aiohttp сервер для webhook ЮKassa
  - Graceful shutdown

## Тестирование

- [ ] Запустить бота локально, проверить все команды
- [ ] Проверить регистрацию нового пользователя
- [ ] Проверить все три типа проверок с моковыми данными
- [ ] Проверить списание и отображение баланса
- [ ] Проверить админ-команды
- [ ] Проверить что при недостатке баланса проверка не проходит
- [ ] Проверить ручное пополнение через админку

## Финализация

- [ ] Написать README.md: описание, установка, настройка .env, деплой, инструкция по подключению API и ЮKassa
- [ ] Makefile: `make install` (venv + pip install), `make run` (запуск бота), `make all` (install + run)
- [ ] Проверить .gitignore
- [ ] Финальный коммит
