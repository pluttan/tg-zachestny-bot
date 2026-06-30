![Header](header.png)

<div align="center">

# tg-zachestny-bot

**Counterparty verification bot for Telegram**

[![License](https://img.shields.io/badge/license-MIT-2C2C2C?style=for-the-badge&labelColor=1E1E1E)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-2C2C2C?style=for-the-badge&logo=python&labelColor=1E1E1E)]()
[![Telegram](https://img.shields.io/badge/telegram-bot-2C2C2C?style=for-the-badge&logo=telegram&labelColor=1E1E1E)]()
[![aiogram](https://img.shields.io/badge/aiogram-3.x-2C2C2C?style=for-the-badge&labelColor=1E1E1E)]()

</div>

Telegram bot for verifying legal entities, individuals, and sole proprietors via the zachestnyibiznes.ru API. Acts as a retail frontend over the API — each check is a separate paid order: the user pays per check through YooKassa, then enters the query and receives a formatted report. Includes admin tools for statistics, user listing, and broadcasts. Provider abstractions ship with mock data, so the bot runs end-to-end without real API or payment credentials.

## ■ Features

- ❖ **Entity verification** — check legal entities (ЮЛ) by free-text query (INN, OGRN, or name)
- ❖ **Individual verification** — check individuals (ФЛ) by name + DOB or document data
- ❖ **Sole proprietor verification** — check sole proprietors (ИП) by INN or OGRNIP
- ❖ **Pay-per-check billing** — one YooKassa payment per check; data is entered only after payment confirms
- ❖ **Check history** — per-user log of past checks with full result re-rendering
- ❖ **Configurable prices** — separate price per check type (ЮЛ / ФЛ / ИП)
- ❖ **Admin tools** — usage statistics (day/week/month), paginated user list, broadcast, free checks for admins
- ❖ **Swappable providers** — abstract API and payment interfaces with mock implementations, ready for real swap
- ❖ **YooKassa integration** — payment creation, aiohttp webhook receiver, and status polling fallback

## ■ Stack

| Component | Technology |
|-----------|------------|
| Bot | Python (aiogram 3.x) |
| Async HTTP / webhooks | aiohttp |
| Database | SQLite (aiosqlite) |
| Payments | YooKassa SDK |
| Data API | zachestnyibiznes.ru |
| Config | pydantic-settings (.env) |

## ■ Repository Structure

```
bot/
├── main.py              # entrypoint: wires providers, runs polling + webhook server
├── config.py            # pydantic-settings config (prices, tokens, webhook)
├── texts_data.py        # all bot copy (Russian)
├── handlers/            # user, admin, payment-webhook routers
├── services/            # api_client, payment (YooKassa/mock), billing
├── database/            # SQLite schema, connection, queries
├── utils/               # keyboards, formatters, text helper
├── Makefile             # install / run targets
└── requirements.txt
```

## ■ Usage

```bash
cd bot
make install
make run

# Configure bot/.env (see .env.example):
# BOT_TOKEN, ADMIN_IDS, CHECK_PRICE_UL/FL/IP,
# YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY,
# ZACHESTNY_API_KEY, WEBHOOK_PORT
#
# Without YOOKASSA_* keys → MockPaymentProvider (payments disabled).
# Without ZACHESTNY_API_KEY → MockAPIClient (demo mode).
```

## ■ Screenshots

![Screenshot](screenshots/main.png)

## ■ License

MIT © [pluttan](https://github.com/pluttan)
