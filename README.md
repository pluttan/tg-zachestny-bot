<div align="center">

# tg-zachestny-bot

**Counterparty verification bot for Telegram**


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

<div align="center">

| Component | Technology |
|-----------|------------|
| Bot | Python (aiogram 3.x) |
| Async HTTP / webhooks | aiohttp |
| Database | SQLite (aiosqlite) |
| Payments | YooKassa SDK |
| Data API | zachestnyibiznes.ru |
| Config | pydantic-settings (.env) |

</div>

## ■ How It Works

```
1. User selects a check type — legal entity (ЮЛ), individual (ФЛ), or sole proprietor (ИП)
2. Bot creates a YooKassa payment for the corresponding price; user completes it inside Telegram
3. On payment confirmation (webhook or status-polling fallback), bot prompts the user for the query
4. Bot forwards the query to the zachestnyibiznes.ru API and formats the response
5. Formatted report is delivered to the user and saved to per-user check history for re-rendering
```

## ■ Screenshots

<div align="center">

![Screenshot](screenshots/main.png)

*Main bot interface*

</div>

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

## ■ License

MIT © [pluttan](https://github.com/pluttan)
