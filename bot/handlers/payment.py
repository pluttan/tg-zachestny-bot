import json
import logging

from aiohttp import web

from services.billing import BillingService
from utils.texts import t

logger = logging.getLogger(__name__)

CHECK_TYPE_PROMPTS = {
    "fl": t("payment_prompt_fl"),
    "ul": t("payment_prompt_ul"),
    "ip": t("payment_prompt_ip"),
}


def create_payment_app(billing: BillingService, bot, dp) -> web.Application:
    """Создать aiohttp-приложение для обработки webhook ЮКасса."""
    app = web.Application()
    app["billing"] = billing
    app["bot"] = bot
    app["dp"] = dp
    app.router.add_post("/payment/webhook", handle_payment_webhook)
    return app


async def handle_payment_webhook(request: web.Request) -> web.Response:
    """Обработка webhook от ЮКасса."""
    billing: BillingService = request.app["billing"]
    bot = request.app["bot"]
    dp = request.app["dp"]

    try:
        data = await request.json()
    except json.JSONDecodeError:
        return web.Response(status=400, text="Invalid JSON")

    logger.info(f"Payment webhook received: {json.dumps(data, ensure_ascii=False)[:500]}")

    try:
        result = await billing.payment_provider.handle_webhook(data)
    except NotImplementedError:
        logger.info("Payment provider not implemented, ignoring webhook")
        return web.Response(status=200, text="OK")
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return web.Response(status=500, text="Internal error")

    if result is None:
        return web.Response(status=200, text="OK")

    payment_id = result["payment_id"]

    # Пометить платёж как оплаченный
    payment = await billing.mark_payment_paid(payment_id)
    if payment is None:
        return web.Response(status=200, text="OK")

    tg_id = payment["tg_id"]
    check_type = payment["check_type"]

    # Отправить сообщение с просьбой ввести данные
    try:
        prompt = CHECK_TYPE_PROMPTS.get(check_type, t("payment_prompt_default"))

        await bot.send_message(tg_id, prompt, parse_mode="HTML")

        # Установить FSM-состояние через storage
        from aiogram.fsm.context import FSMContext
        from aiogram.fsm.storage.base import StorageKey
        from handlers.user import CheckStates

        key = StorageKey(bot_id=bot.id, chat_id=tg_id, user_id=tg_id)
        ctx = FSMContext(storage=dp.storage, key=key)
        await ctx.set_state(CheckStates.waiting_query)

        logger.info(f"Payment confirmed, waiting for query: tg_id={tg_id}, type={check_type}")

    except Exception as e:
        logger.error(f"Could not notify user {tg_id}: {e}")

    return web.Response(status=200, text="OK")
