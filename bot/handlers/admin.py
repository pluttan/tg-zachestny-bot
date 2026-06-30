import logging

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from config import Settings
from database.db import get_db
from database import queries
from utils.keyboards import (
    admin_panel_kb, admin_users_pagination_kb,
    confirm_broadcast_kb, cancel_kb,
)
from utils.formatters import format_stats
from utils.texts import t

logger = logging.getLogger(__name__)

router = Router()


class AdminStates(StatesGroup):
    waiting_broadcast_text = State()


def _is_admin(user_id: int, config: Settings) -> bool:
    return user_id in config.ADMIN_IDS


# === Главная панель ===


@router.message(Command("admin"))
async def cmd_admin(message: Message, config: Settings):
    if not _is_admin(message.from_user.id, config):
        await message.answer(t("admin_no_access"))
        return

    await message.answer(t("admin_panel_title"), reply_markup=admin_panel_kb(), parse_mode="HTML")


@router.callback_query(F.data == "admin:panel")
async def cb_admin_panel(callback: CallbackQuery, config: Settings, state: FSMContext):
    if not _is_admin(callback.from_user.id, config):
        await callback.answer(t("admin_no_access"))
        return

    await state.clear()
    await callback.message.edit_text(
        t("admin_panel_title"), reply_markup=admin_panel_kb(), parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "admin:close")
async def cb_admin_close(callback: CallbackQuery, config: Settings):
    if not _is_admin(callback.from_user.id, config):
        await callback.answer(t("admin_no_access"))
        return

    await callback.message.delete()
    await callback.answer()


# === Статистика ===


@router.callback_query(F.data == "admin:stats")
async def cb_admin_stats(callback: CallbackQuery, config: Settings):
    if not _is_admin(callback.from_user.id, config):
        await callback.answer(t("admin_no_access"))
        return

    db = await get_db()
    stats_day = await queries.get_stats(db, "day")
    stats_week = await queries.get_stats(db, "week")
    stats_month = await queries.get_stats(db, "month")

    text = (
        f"{format_stats(stats_day)}\n\n"
        f"{format_stats(stats_week)}\n\n"
        f"{format_stats(stats_month)}"
    )
    await callback.message.edit_text(
        text, reply_markup=admin_back_kb(), parse_mode="HTML"
    )
    await callback.answer()


# === Пользователи ===


@router.callback_query(F.data == "admin:users")
async def cb_admin_users(callback: CallbackQuery, config: Settings):
    if not _is_admin(callback.from_user.id, config):
        await callback.answer(t("admin_no_access"))
        return

    db = await get_db()
    total = await queries.get_user_count(db)
    users = await queries.get_all_users(db, offset=0, limit=20)

    text = _format_users_list(users, 0, total)
    kb = admin_users_pagination_kb(0, total)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_users:"))
async def cb_admin_users_page(callback: CallbackQuery, config: Settings):
    if not _is_admin(callback.from_user.id, config):
        await callback.answer(t("admin_no_access"))
        return

    offset = int(callback.data.split(":")[1])
    db = await get_db()
    total = await queries.get_user_count(db)
    users = await queries.get_all_users(db, offset=offset, limit=20)

    text = _format_users_list(users, offset, total)
    kb = admin_users_pagination_kb(offset, total)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


# === Рассылка ===


@router.callback_query(F.data == "admin:broadcast")
async def cb_admin_broadcast(callback: CallbackQuery, config: Settings, state: FSMContext):
    if not _is_admin(callback.from_user.id, config):
        await callback.answer(t("admin_no_access"))
        return

    await state.set_state(AdminStates.waiting_broadcast_text)
    await callback.message.edit_text(
        t("admin_broadcast_prompt"), reply_markup=admin_back_kb(), parse_mode="HTML"
    )
    await callback.answer()


@router.message(AdminStates.waiting_broadcast_text)
async def process_broadcast_text(message: Message, state: FSMContext):
    text = message.text
    if not text:
        await message.answer(t("admin_broadcast_enter_text"))
        return

    await state.update_data(broadcast_text=text)
    await state.clear()

    db = await get_db()
    total = await queries.get_user_count(db)

    await message.answer(
        t("admin_broadcast_preview", text=text, total=total),
        reply_markup=confirm_broadcast_kb(),
        parse_mode="HTML",
    )
    await state.update_data(broadcast_text=text)


@router.callback_query(F.data == "broadcast:confirm")
async def cb_broadcast_confirm(
    callback: CallbackQuery, config: Settings, bot: Bot, state: FSMContext
):
    if not _is_admin(callback.from_user.id, config):
        await callback.answer(t("admin_no_access"))
        return

    data = await state.get_data()
    text = data.get("broadcast_text")
    await state.clear()

    if not text:
        await callback.message.edit_text(t("admin_broadcast_no_text"))
        await callback.answer()
        return

    db = await get_db()
    tg_ids = await queries.get_all_tg_ids(db)

    await callback.message.edit_text(t("admin_broadcast_started"))

    sent = 0
    failed = 0
    for tg_id in tg_ids:
        try:
            await bot.send_message(tg_id, text, parse_mode="HTML")
            sent += 1
        except Exception as e:
            logger.warning(f"Broadcast failed for {tg_id}: {e}")
            failed += 1

    await callback.message.answer(
        t("admin_broadcast_done", sent=sent, failed=failed),
        reply_markup=admin_back_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


# === Утилиты ===


def admin_back_kb():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=t("btn_admin_back"), callback_data="admin:panel"),
    )
    return builder.as_markup()


def _format_users_list(users: list[dict], offset: int, total: int) -> str:
    lines = [t("admin_users_title", start=offset + 1, end=offset + len(users), total=total)]
    for u in users:
        username = f"@{u['username']}" if u["username"] else "—"
        lines.append(
            f"  ID: <code>{u['tg_id']}</code> | {username} | {u['created_at'][:10]}"
        )
    return "\n".join(lines)
