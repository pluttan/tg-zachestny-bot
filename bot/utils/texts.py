from texts_data import TEXTS


def t(key: str, **kwargs) -> str:
    """Получить текст по ключу с подстановкой параметров."""
    value = TEXTS.get(key, key)
    if isinstance(value, str) and kwargs:
        return value.format(**kwargs)
    return value if isinstance(value, str) else str(value)


def t_raw(key: str):
    """Получить значение по ключу без форматирования (для dict и т.д.)."""
    return TEXTS.get(key, key)
