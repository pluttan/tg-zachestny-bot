import asyncio
import logging
import uuid
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BasePaymentProvider(ABC):
    @abstractmethod
    async def create_payment(
        self, amount: float, description: str, tg_id: int
    ) -> dict:
        """
        Создать платёж.
        Возвращает {"url": str | None, "payment_id": str | None, "message": str}
        """
        pass

    @abstractmethod
    async def handle_webhook(self, data: dict) -> dict | None:
        """
        Обработать webhook от платёжной системы.
        Возвращает {"tg_id": int, "amount": float, "payment_id": str} или None
        """
        pass

    async def check_payment_status(self, payment_id: str) -> str | None:
        """Проверить статус платежа. Возвращает статус или None."""
        return None


class MockPaymentProvider(BasePaymentProvider):
    async def create_payment(
        self, amount: float, description: str, tg_id: int
    ) -> dict:
        return {
            "url": None,
            "payment_id": None,
            "message": (
                "Автоматическая оплата временно недоступна.\n\n"
                "Для пополнения баланса обратитесь к администратору."
            ),
        }

    async def handle_webhook(self, data: dict) -> dict | None:
        return None


class YooKassaProvider(BasePaymentProvider):
    """
    Провайдер оплаты через ЮКасса.
    Документация: https://yookassa.ru/developers/api
    """

    def __init__(self, shop_id: str, secret_key: str, return_url: str = "https://t.me"):
        from yookassa import Configuration
        Configuration.account_id = shop_id
        Configuration.secret_key = secret_key
        self.shop_id = shop_id
        self.secret_key = secret_key
        self.return_url = return_url

    async def create_payment(
        self, amount: float, description: str, tg_id: int
    ) -> dict:
        from yookassa import Payment

        try:
            idempotency_key = str(uuid.uuid4())
            payment = await asyncio.to_thread(
                Payment.create,
                {
                    "amount": {
                        "value": f"{amount:.2f}",
                        "currency": "RUB",
                    },
                    "confirmation": {
                        "type": "redirect",
                        "return_url": self.return_url,
                    },
                    "capture": True,
                    "description": description,
                    "metadata": {
                        "tg_id": str(tg_id),
                    },
                },
                idempotency_key,
            )

            payment_url = payment.confirmation.confirmation_url
            payment_id = payment.id

            logger.info(f"Payment created: id={payment_id}, amount={amount}, tg_id={tg_id}")

            return {
                "url": payment_url,
                "payment_id": payment_id,
                "message": f"Для оплаты перейдите по ссылке ниже.",
            }

        except Exception as e:
            logger.error(f"YooKassa create_payment error: {e}")
            return {
                "url": None,
                "payment_id": None,
                "message": (
                    f"Ошибка создания платежа: {e}\n\n"
                    "Для пополнения баланса обратитесь к администратору."
                ),
            }

    async def handle_webhook(self, data: dict) -> dict | None:
        """
        Обработка webhook от ЮКасса.

        Формат входящих данных:
        {
            "type": "notification",
            "event": "payment.succeeded",
            "object": {
                "id": "...",
                "status": "succeeded",
                "amount": {"value": "100.00", "currency": "RUB"},
                "metadata": {"tg_id": "123456"}
            }
        }
        """
        try:
            event = data.get("event", "")
            obj = data.get("object", {})
            payment_id = obj.get("id")
            status = obj.get("status")

            logger.info(f"YooKassa webhook: event={event}, payment_id={payment_id}, status={status}")

            if event != "payment.succeeded" or status != "succeeded":
                logger.info(f"Ignoring webhook event: {event}, status: {status}")
                return None

            amount_data = obj.get("amount", {})
            amount = float(amount_data.get("value", 0))

            metadata = obj.get("metadata", {})
            tg_id = int(metadata.get("tg_id", 0))

            if not tg_id or not amount:
                logger.warning(f"Webhook missing tg_id or amount: tg_id={tg_id}, amount={amount}")
                return None

            return {
                "tg_id": tg_id,
                "amount": amount,
                "payment_id": payment_id,
            }

        except Exception as e:
            logger.error(f"YooKassa webhook processing error: {e}")
            return None

    async def check_payment_status(self, payment_id: str) -> str | None:
        from yookassa import Payment

        try:
            payment = await asyncio.to_thread(Payment.find_one, payment_id)
            return payment.status
        except Exception as e:
            logger.error(f"YooKassa check_payment_status error: {e}")
            return None
