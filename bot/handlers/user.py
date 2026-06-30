import asyncio
import logging

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import Message, CallbackQuery

from config import Settings
from database.db import get_db
from database import queries
from services.billing import BillingService
from utils.keyboards import (
    main_menu_kb,
    confirm_check_kb,
    payment_link_kb,
    history_kb,
    back_to_menu_kb,
    cancel_kb,
    help_kb,
    help_back_kb,
)
from utils.formatters import (
    format_fl_result,
    format_ul_result,
    format_ip_result,
    format_prices,
)
from utils.texts import t, t_raw

logger = logging.getLogger(__name__)

router = Router()


class CheckStates(StatesGroup):
    waiting_query = State()


CHECK_TYPE_PROMPTS = {
    "fl": t("payment_prompt_fl"),
    "ul": t("payment_prompt_ul"),
    "ip": t("payment_prompt_ip"),
}

CHECK_TYPE_NAMES = t_raw("check_type_names")


def _welcome_text(config) -> str:
    return t("welcome",
        price_fl=f"{config.CHECK_PRICE_FL:.0f}",
        price_ul=f"{config.CHECK_PRICE_UL:.0f}",
        price_ip=f"{config.CHECK_PRICE_IP:.0f}",
    )


HELP_TEXT = t("help")

HELP_FL_TEXT = t("help_fl")

HELP_UL_TEXT = t("help_ul")

HELP_IP_TEXT = t("help_ip")


# === Команды ===


@router.message(CommandStart())
async def cmd_start(message: Message, billing: BillingService, state: FSMContext, bot_username: str = ""):
    await state.clear()
    db = await get_db()
    await queries.get_or_create_user(
        db,
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name,
    )
    text = _welcome_text(billing.config)
    await message.answer(text, reply_markup=main_menu_kb(bot_username), parse_mode="HTML")


@router.message(Command("help"))
@router.message(Command("faq"))
async def cmd_help(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(HELP_TEXT, reply_markup=help_kb(), parse_mode="HTML")


@router.message(Command("prices"))
async def cmd_prices(message: Message, billing: BillingService, state: FSMContext):
    await state.clear()
    text = format_prices(billing.config)
    await message.answer(text, reply_markup=back_to_menu_kb(), parse_mode="HTML")


@router.message(Command("history"))
async def cmd_history(message: Message, state: FSMContext):
    await state.clear()
    db = await get_db()
    checks = await queries.get_checks_history(db, message.from_user.id, limit=10)
    if not checks:
        await message.answer(
            t("history_empty"), reply_markup=back_to_menu_kb(), parse_mode="HTML"
        )
        return
    await message.answer(
        t("history_title"),
        reply_markup=history_kb(checks),
        parse_mode="HTML",
    )


CHECK_SCREEN_FL = t_raw("check_screen_fl")


@router.message(Command("check_fl"))
async def cmd_check_fl(message: Message, billing: BillingService, state: FSMContext, config: Settings):
    await state.clear()
    price = billing.config.CHECK_PRICE_FL
    await message.answer(
        CHECK_SCREEN_FL.format(price=f"{price:.0f}"),
        reply_markup=confirm_check_kb("fl", price, message.from_user.id in config.ADMIN_IDS),
        parse_mode="HTML",
    )


CHECK_SCREEN_UL = t_raw("check_screen_ul")


@router.message(Command("check_ul"))
async def cmd_check_ul(message: Message, billing: BillingService, state: FSMContext, config: Settings):
    await state.clear()
    price = billing.config.CHECK_PRICE_UL
    await message.answer(
        CHECK_SCREEN_UL.format(price=f"{price:.0f}"),
        reply_markup=confirm_check_kb("ul", price, message.from_user.id in config.ADMIN_IDS),
        parse_mode="HTML",
    )


CHECK_SCREEN_IP = t_raw("check_screen_ip")


@router.message(Command("check_ip"))
async def cmd_check_ip(message: Message, billing: BillingService, state: FSMContext, config: Settings):
    await state.clear()
    price = billing.config.CHECK_PRICE_IP
    await message.answer(
        CHECK_SCREEN_IP.format(price=f"{price:.0f}"),
        reply_markup=confirm_check_kb("ip", price, message.from_user.id in config.ADMIN_IDS),
        parse_mode="HTML",
    )


# === Ввод данных после оплаты ===


@router.message(CheckStates.waiting_query)
async def process_paid_query(message: Message, billing: BillingService, state: FSMContext):
    query = message.text.strip()
    if not query:
        await message.answer(t("check_enter_data"))
        return

    await state.clear()
    processing_msg = await message.answer(t("check_processing"), parse_mode="HTML")

    result = await billing.execute_paid_check(message.from_user.id, query)

    await processing_msg.delete()

    if not result["success"]:
        await message.answer(
            result["error"], reply_markup=back_to_menu_kb(), parse_mode="HTML"
        )
        return

    check_type = result["check_type"]
    data = result["result"]
    if data.get("_mock"):
        text = f"✅ <b>Запрос принят (демо-режим)</b>\n\n{data['query']}"
    elif check_type == "fl":
        text = format_fl_result(data)
    elif check_type == "ul":
        text = format_ul_result(data)
    elif check_type == "ip":
        text = format_ip_result(data)
    else:
        text = str(data)

    if len(text) > 4000:
        parts = [text[i : i + 4000] for i in range(0, len(text), 4000)]
        for part in parts:
            await message.answer(part, parse_mode="HTML")
        await message.answer(
            t("check_done"), reply_markup=back_to_menu_kb(), parse_mode="HTML"
        )
    else:
        await message.answer(text, reply_markup=back_to_menu_kb(), parse_mode="HTML")


# === Callback-хэндлеры меню ===


@router.callback_query(F.data == "menu:main")
async def cb_main_menu(callback: CallbackQuery, billing: BillingService, state: FSMContext, bot_username: str = ""):
    await state.clear()
    text = _welcome_text(billing.config)
    await callback.message.edit_text(
        text, reply_markup=main_menu_kb(bot_username), parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "menu:check_fl")
async def cb_check_fl(callback: CallbackQuery, billing: BillingService, state: FSMContext, config: Settings):
    await state.clear()
    price = billing.config.CHECK_PRICE_FL
    await callback.message.edit_text(
        CHECK_SCREEN_FL.format(price=f"{price:.0f}"),
        reply_markup=confirm_check_kb("fl", price, callback.from_user.id in config.ADMIN_IDS),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "menu:check_ul")
async def cb_check_ul(callback: CallbackQuery, billing: BillingService, state: FSMContext, config: Settings):
    await state.clear()
    price = billing.config.CHECK_PRICE_UL
    await callback.message.edit_text(
        CHECK_SCREEN_UL.format(price=f"{price:.0f}"),
        reply_markup=confirm_check_kb("ul", price, callback.from_user.id in config.ADMIN_IDS),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "menu:check_ip")
async def cb_check_ip(callback: CallbackQuery, billing: BillingService, state: FSMContext, config: Settings):
    await state.clear()
    price = billing.config.CHECK_PRICE_IP
    await callback.message.edit_text(
        CHECK_SCREEN_IP.format(price=f"{price:.0f}"),
        reply_markup=confirm_check_kb("ip", price, callback.from_user.id in config.ADMIN_IDS),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "menu:history")
async def cb_history(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    db = await get_db()
    checks = await queries.get_checks_history(db, callback.from_user.id, limit=10)
    if not checks:
        await callback.message.edit_text(
            t("history_empty"),
            reply_markup=back_to_menu_kb(),
            parse_mode="HTML",
        )
    else:
        await callback.message.edit_text(
            t("history_title"),
            reply_markup=history_kb(checks),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data == "menu:prices")
async def cb_prices(callback: CallbackQuery, billing: BillingService, state: FSMContext):
    await state.clear()
    text = format_prices(billing.config)
    await callback.message.edit_text(
        text, reply_markup=back_to_menu_kb(), parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "menu:help")
async def cb_help(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        HELP_TEXT, reply_markup=help_kb(), parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "help:fl")
async def cb_help_fl(callback: CallbackQuery):
    await callback.message.edit_text(
        HELP_FL_TEXT, reply_markup=help_back_kb(), parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "help:ul")
async def cb_help_ul(callback: CallbackQuery):
    await callback.message.edit_text(
        HELP_UL_TEXT, reply_markup=help_back_kb(), parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "help:ip")
async def cb_help_ip(callback: CallbackQuery):
    await callback.message.edit_text(
        HELP_IP_TEXT, reply_markup=help_back_kb(), parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "cancel")
async def cb_cancel(callback: CallbackQuery, billing: BillingService, state: FSMContext, bot_username: str = ""):
    await state.clear()
    text = _welcome_text(billing.config)
    await callback.message.edit_text(
        text, reply_markup=main_menu_kb(bot_username), parse_mode="HTML"
    )
    await callback.answer(t("cancelled"))


# === Оплата проверки ===


async def _poll_payment(
    bot: Bot,
    storage,
    billing: BillingService,
    tg_id: int,
    payment_id: str,
    check_type: str,
    chat_id: int,
    message_id: int,
):
    """Поллинг статуса платежа через API ЮКасса."""
    for _ in range(60):  # ~10 минут (каждые 10 секунд)
        await asyncio.sleep(10)
        try:
            status = await billing.payment_provider.check_payment_status(payment_id)
        except Exception as e:
            logger.error(f"Payment poll error: {e}")
            continue

        if status == "succeeded":
            payment = await billing.mark_payment_paid(payment_id)
            if payment:
                # Удаляем сообщение с платёжной ссылкой
                try:
                    await bot.delete_message(chat_id=chat_id, message_id=message_id)
                except Exception as e:
                    logger.warning(f"Could not delete payment message: {e}")

                prompt = CHECK_TYPE_PROMPTS.get(check_type, t("payment_prompt_default"))
                await bot.send_message(tg_id, prompt, parse_mode="HTML")
                key = StorageKey(bot_id=bot.id, chat_id=tg_id, user_id=tg_id)
                ctx = FSMContext(storage=storage, key=key)
                await ctx.set_state(CheckStates.waiting_query)
                logger.info(f"Payment confirmed via polling: {payment_id}, tg_id={tg_id}")
            return
        elif status in ("canceled", "refunded"):
            logger.info(f"Payment {status} via polling: {payment_id}")
            return

    logger.warning(f"Payment poll timeout: {payment_id}")


@router.callback_query(F.data.startswith("confirm_check:"))
async def cb_confirm_check(
    callback: CallbackQuery, billing: BillingService, state: FSMContext
):
    check_type = callback.data.split(":")[1]
    await state.clear()
    await callback.message.edit_text(t("payment_creating"), parse_mode="HTML")

    result = await billing.create_check_payment(callback.from_user.id, check_type)

    if result.get("url"):
        price = billing.config.get_check_price(check_type)
        type_name = CHECK_TYPE_NAMES.get(check_type, check_type)
        await callback.message.edit_text(
            t("payment_link", type_name=type_name, price=f"{price:.0f}", url=result['url']),
            reply_markup=payment_link_kb(result['url']),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        # Запуск поллинга статуса платежа через API ЮКасса
        asyncio.create_task(
            _poll_payment(
                callback.bot,
                state.storage,
                billing,
                callback.from_user.id,
                result["payment_id"],
                check_type,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
            )
        )
    else:
        await callback.message.edit_text(
            result["message"],
            reply_markup=back_to_menu_kb(),
            parse_mode="HTML",
        )

    await callback.answer()


@router.callback_query(F.data.startswith("free_check:"))
async def cb_free_check(callback: CallbackQuery, state: FSMContext, config: Settings):
    check_type = callback.data.split(":")[1]
    if callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer(t("admin_no_access"))
        return

    import uuid
    fake_payment_id = f"admin_{uuid.uuid4().hex[:12]}"
    price = config.get_check_price(check_type)
    db = await get_db()
    await queries.create_payment(db, callback.from_user.id, price, fake_payment_id, check_type)
    await queries.update_payment_status(db, fake_payment_id, "paid")

    prompt = CHECK_TYPE_PROMPTS.get(check_type, t("payment_prompt_default"))
    await state.set_state(CheckStates.waiting_query)
    await callback.message.edit_text(prompt, parse_mode="HTML")
    await callback.answer()


# === Просмотр проверки из истории ===


@router.callback_query(F.data.startswith("view_check:"))
async def cb_view_check(callback: CallbackQuery):
    check_id = int(callback.data.split(":")[1])
    db = await get_db()
    check = await queries.get_check_by_id(db, check_id)

    if not check:
        await callback.message.edit_text(
            t("check_not_found"), reply_markup=back_to_menu_kb(), parse_mode="HTML"
        )
        await callback.answer()
        return

    check_type = check["check_type"]
    result = check["result"]

    if check_type == "fl":
        text = format_fl_result(result)
    elif check_type == "ul":
        text = format_ul_result(result)
    elif check_type == "ip":
        text = format_ip_result(result)
    else:
        text = str(result)

    if len(text) > 4000:
        parts = [text[i : i + 4000] for i in range(0, len(text), 4000)]
        for i, part in enumerate(parts):
            if i == 0:
                await callback.message.edit_text(part, parse_mode="HTML")
            else:
                await callback.message.answer(part, parse_mode="HTML")
        await callback.message.answer(
            t("check_end_report"), reply_markup=back_to_menu_kb(), parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            text, reply_markup=back_to_menu_kb(), parse_mode="HTML"
        )

    await callback.answer()
