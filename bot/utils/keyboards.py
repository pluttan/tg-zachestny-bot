from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.texts import t


def main_menu_kb(bot_username: str = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=t("btn_check_fl"), callback_data="menu:check_fl"),
        InlineKeyboardButton(text=t("btn_check_ul"), callback_data="menu:check_ul"),
    )
    builder.row(
        InlineKeyboardButton(text=t("btn_check_ip"), callback_data="menu:check_ip"),
    )
    builder.row(
        InlineKeyboardButton(text=t("btn_history"), callback_data="menu:history"),
        InlineKeyboardButton(text=t("btn_prices"), callback_data="menu:prices"),
    )
    if bot_username:
        builder.row(
            InlineKeyboardButton(
                text=t("btn_add_group"),
                url=f"https://t.me/{bot_username}?startgroup=true",
            ),
        )
    builder.row(
        InlineKeyboardButton(text=t("btn_help"), callback_data="menu:help"),
    )
    return builder.as_markup()



def confirm_check_kb(check_type: str, cost: float, is_admin: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=t("btn_pay", price=f"{cost:.0f}"),
            callback_data=f"confirm_check:{check_type}",
        ),
    )
    if is_admin:
        builder.row(
            InlineKeyboardButton(
                text=t("btn_free_check"),
                callback_data=f"free_check:{check_type}",
            ),
        )
    builder.row(
        InlineKeyboardButton(text=t("btn_back"), callback_data="cancel"),
    )
    return builder.as_markup()


def history_kb(checks: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    type_names = {"ul": "ЮЛ", "fl": "ФЛ", "ip": "ИП"}
    for check in checks:
        check_id = check["id"]
        check_type = type_names.get(check["check_type"], check["check_type"])
        query_short = check["query"][:30]
        builder.row(
            InlineKeyboardButton(
                text=f"[{check_type}] {query_short}",
                callback_data=f"view_check:{check_id}",
            )
        )
    builder.row(
        InlineKeyboardButton(text=t("btn_history_back"), callback_data="menu:main"),
    )
    return builder.as_markup()


def payment_link_kb(url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=t("btn_go_to_payment"), url=url),
    )
    builder.row(
        InlineKeyboardButton(text=t("btn_main_menu"), callback_data="menu:main"),
    )
    return builder.as_markup()


def back_to_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=t("btn_main_menu"), callback_data="menu:main"),
    )
    return builder.as_markup()


def help_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=t("btn_help_fl"), callback_data="help:fl"),
    )
    builder.row(
        InlineKeyboardButton(text=t("btn_help_ul"), callback_data="help:ul"),
    )
    builder.row(
        InlineKeyboardButton(text=t("btn_help_ip"), callback_data="help:ip"),
    )
    builder.row(
        InlineKeyboardButton(text=t("btn_main_menu"), callback_data="menu:main"),
    )
    return builder.as_markup()


def help_back_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=t("btn_back_help"), callback_data="menu:help"),
    )
    return builder.as_markup()


def admin_panel_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=t("btn_admin_stats"), callback_data="admin:stats"),
    )
    builder.row(
        InlineKeyboardButton(text=t("btn_admin_users"), callback_data="admin:users"),
    )
    builder.row(
        InlineKeyboardButton(text=t("btn_admin_broadcast"), callback_data="admin:broadcast"),
    )
    builder.row(
        InlineKeyboardButton(text=t("btn_admin_close"), callback_data="admin:close"),
    )
    return builder.as_markup()


def admin_users_pagination_kb(offset: int, total: int, page_size: int = 20) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    buttons = []
    if offset > 0:
        buttons.append(
            InlineKeyboardButton(text=t("btn_page_prev"), callback_data=f"admin_users:{offset - page_size}")
        )
    if offset + page_size < total:
        buttons.append(
            InlineKeyboardButton(text=t("btn_page_next"), callback_data=f"admin_users:{offset + page_size}")
        )
    if buttons:
        builder.row(*buttons)
    builder.row(
        InlineKeyboardButton(text=t("btn_admin_back"), callback_data="admin:panel"),
    )
    return builder.as_markup()


def cancel_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=t("btn_cancel"), callback_data="cancel"),
    )
    return builder.as_markup()


def confirm_broadcast_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=t("btn_send_all"), callback_data="broadcast:confirm"),
        InlineKeyboardButton(text=t("btn_cancel"), callback_data="cancel"),
    )
    return builder.as_markup()
