import asyncio
from abc import ABC, abstractmethod


class BaseAPIClient(ABC):
    @abstractmethod
    async def check_ul(self, query: str) -> dict:
        pass

    @abstractmethod
    async def check_fl(self, query: str) -> dict:
        pass

    @abstractmethod
    async def check_ip(self, query: str) -> dict:
        pass


class MockAPIClient(BaseAPIClient):
    async def check_ul(self, query: str) -> dict:
        return {"_mock": True, "query": query}

    async def check_fl(self, query: str) -> dict:
        return {"_mock": True, "query": query}

    async def check_ip(self, query: str) -> dict:
        return {"_mock": True, "query": query}


class ZachestnyAPIClient(BaseAPIClient):
    """
    Реальный клиент API zachestnyibiznes.ru
    Подключается когда будет доступен API-ключ.

    Base URL (ЮЛ/ИП): https://zachestnyibiznesapi.ru/paid/data/{method}?api_key={key}
    Base URL (ФЛ): https://zachestnyibiznesapi.ru/flcheck/data/{method}?api_key={key}

    Формат ответа: {"status": "...", "message": "...", "body": {...}}

    ФЛ работает асинхронно:
    1. Отправить запрос на проверку
    2. Дождаться формирования отчёта (список отчётов на формировании)
    3. Получить готовый отчёт
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://zachestnyibiznesapi.ru"

    async def check_ul(self, query: str) -> dict:
        # TODO: реализовать запрос к API
        # GET {base_url}/paid/data/search?api_key={key}&string={query}
        raise NotImplementedError("API zachestnyibiznes не подключен")

    async def check_fl(self, query: str) -> dict:
        # TODO: реализовать асинхронный запрос к API
        # 1. POST {base_url}/flcheck/data/request?api_key={key} - создать запрос
        # 2. GET {base_url}/flcheck/data/pending?api_key={key} - проверить статус
        # 3. GET {base_url}/flcheck/data/report?api_key={key}&id={id} - получить отчёт
        raise NotImplementedError("API zachestnyibiznes не подключен")

    async def check_ip(self, query: str) -> dict:
        # TODO: реализовать запрос к API
        # GET {base_url}/paid/data/ip?api_key={key}&string={query}
        raise NotImplementedError("API zachestnyibiznes не подключен")
