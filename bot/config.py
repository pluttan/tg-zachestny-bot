from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Optional


class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_IDS_RAW: str = Field("", alias="ADMIN_IDS")

    CHECK_PRICE_UL: float = 300.0
    CHECK_PRICE_FL: float = 300.0
    CHECK_PRICE_IP: float = 300.0
    MIN_TOPUP: float = 100.0

    YOOKASSA_SHOP_ID: Optional[str] = None
    YOOKASSA_SECRET_KEY: Optional[str] = None

    ZACHESTNY_API_KEY: Optional[str] = None

    WEBHOOK_HOST: Optional[str] = None
    WEBHOOK_PORT: int = 8080

    DB_PATH: str = "bot.db"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "populate_by_name": True,
    }

    @property
    def ADMIN_IDS(self) -> list[int]:
        raw = self.ADMIN_IDS_RAW.strip()
        if not raw:
            return []
        return [int(x.strip()) for x in raw.split(",") if x.strip()]

    def get_check_price(self, check_type: str) -> float:
        prices = {
            "ul": self.CHECK_PRICE_UL,
            "fl": self.CHECK_PRICE_FL,
            "ip": self.CHECK_PRICE_IP,
        }
        return prices.get(check_type, 0.0)
