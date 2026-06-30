import logging

import aiosqlite

from config import Settings
from database import queries
from services.api_client import BaseAPIClient
from services.payment import BasePaymentProvider

logger = logging.getLogger(__name__)


CHECK_TYPE_NAMES = {
    "ul": "Юридическое лицо",
    "fl": "Физическое лицо",
    "ip": "Индивидуальный предприниматель",
}


class BillingService:
    def __init__(
        self,
        db: aiosqlite.Connection,
        api_client: BaseAPIClient,
        payment_provider: BasePaymentProvider,
        config: Settings,
    ):
        self.db = db
        self.api_client = api_client
        self.payment_provider = payment_provider
        self.config = config

    async def create_check_payment(self, tg_id: int, check_type: str) -> dict:
        """
        Создать платёж за проверку (без запроса — данные вводятся после оплаты).
        Возвращает {"url": str | None, "payment_id": str | None, "message": str}
        """
        price = self.config.get_check_price(check_type)
        type_name = CHECK_TYPE_NAMES.get(check_type, check_type)

        description = f"Проверка: {type_name}"

        result = await self.payment_provider.create_payment(
            amount=price,
            description=description,
            tg_id=tg_id,
        )

        if result.get("payment_id"):
            await queries.create_payment(
                self.db,
                tg_id,
                price,
                result["payment_id"],
                check_type,
            )
            logger.info(
                f"Payment created: tg_id={tg_id}, type={check_type}, "
                f"payment_id={result['payment_id']}"
            )

        return result

    async def mark_payment_paid(self, payment_id: str) -> dict | None:
        """
        Пометить платёж как оплаченный (ожидает ввод данных от пользователя).
        Возвращает данные платежа или None.
        """
        payment = await queries.get_payment_by_id(self.db, payment_id)
        if not payment:
            logger.warning(f"Payment not found: {payment_id}")
            return None

        if payment["status"] != "pending":
            logger.info(f"Payment already processed: {payment_id}, status={payment['status']}")
            return None

        await queries.update_payment_status(self.db, payment_id, "paid")
        logger.info(f"Payment marked as paid: {payment_id}")
        return payment

    async def execute_paid_check(self, tg_id: int, query: str) -> dict:
        """
        Выполнить проверку по оплаченному платежу.
        Находит неиспользованный платёж, выполняет проверку, сохраняет результат.
        """
        payment = await queries.get_paid_unused_payment(self.db, tg_id)
        if not payment:
            return {
                "success": False,
                "result": None,
                "error": "Нет оплаченных проверок. Сначала оплатите проверку.",
            }

        check_type = payment["check_type"]
        payment_id = payment["payment_id"]
        amount = payment["amount"]

        try:
            if check_type == "ul":
                result = await self.api_client.check_ul(query)
            elif check_type == "fl":
                result = await self.api_client.check_fl(query)
            elif check_type == "ip":
                result = await self.api_client.check_ip(query)
            else:
                raise ValueError(f"Неизвестный тип проверки: {check_type}")
        except Exception as e:
            logger.error(f"API error for payment {payment_id}: {e}")
            return {
                "success": False,
                "result": None,
                "error": f"Ошибка API: {e}. Обратитесь к администратору.",
            }

        await queries.set_payment_query_and_complete(self.db, payment_id, query)

        check_id = await queries.save_check(
            self.db, tg_id, check_type, query, result, amount
        )

        logger.info(
            f"Check completed: tg_id={tg_id}, type={check_type}, "
            f"check_id={check_id}, payment_id={payment_id}"
        )

        return {
            "success": True,
            "result": result,
            "check_type": check_type,
            "check_id": check_id,
            "error": None,
        }
