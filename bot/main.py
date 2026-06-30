import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiohttp import web

from config import Settings
from database.db import init_db, close_db
from services.api_client import MockAPIClient, ZachestnyAPIClient
from services.payment import MockPaymentProvider, YooKassaProvider
from services.billing import BillingService
from handlers import user, admin
from handlers.payment import create_payment_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def main():
    # Конфиг
    config = Settings()
    logger.info("Config loaded")

    # БД
    db = await init_db(config.DB_PATH)
    logger.info(f"Database initialized: {config.DB_PATH}")

    # API клиент
    if config.ZACHESTNY_API_KEY:
        api_client = ZachestnyAPIClient(config.ZACHESTNY_API_KEY)
        logger.info("Using ZachestnyAPIClient (real API)")
    else:
        api_client = MockAPIClient()
        logger.info("Using MockAPIClient (demo mode)")

    # Платёжный провайдер
    if config.YOOKASSA_SHOP_ID and config.YOOKASSA_SECRET_KEY:
        payment_provider = YooKassaProvider(
            config.YOOKASSA_SHOP_ID, config.YOOKASSA_SECRET_KEY
        )
        logger.info("Using YooKassaProvider")
    else:
        payment_provider = MockPaymentProvider()
        logger.info("Using MockPaymentProvider (payments disabled)")

    # Биллинг
    billing = BillingService(db, api_client, payment_provider, config)

    # Бот
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    dp = Dispatcher()

    # Регистрация роутеров
    dp.include_router(user.router)
    dp.include_router(admin.router)

    # Получаем username бота для ссылки добавления в группу
    bot_info = await bot.get_me()
    bot_username = bot_info.username

    # Middleware для инъекции зависимостей
    @dp.message.middleware()
    async def inject_deps_message(handler, event, data):
        data["billing"] = billing
        data["config"] = config
        data["bot_username"] = bot_username
        return await handler(event, data)

    @dp.callback_query.middleware()
    async def inject_deps_callback(handler, event, data):
        data["billing"] = billing
        data["config"] = config
        data["bot_username"] = bot_username
        return await handler(event, data)

    # Webhook-сервер для ЮКасса
    payment_app = create_payment_app(billing, bot, dp)

    runner = web.AppRunner(payment_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", config.WEBHOOK_PORT)

    try:
        await site.start()
        logger.info(f"Payment webhook server started on port {config.WEBHOOK_PORT}")

        logger.info("Starting bot polling...")
        await dp.start_polling(bot)
    finally:
        logger.info("Shutting down...")
        await site.stop()
        await runner.cleanup()
        await bot.session.close()
        await close_db()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
