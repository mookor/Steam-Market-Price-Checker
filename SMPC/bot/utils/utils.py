from uuid import UUID, uuid5, NAMESPACE_DNS
from urllib.parse import urlparse, unquote

def telegram_id_to_uuid(telegram_id: int) -> UUID:
    """
    Преобразует Telegram ID в детерминистический UUID.
    Для одного и того же Telegram ID всегда возвращается один и тот же UUID.
    """
    # Используем uuid5 с пространством имен и строковым представлением ID
    namespace = NAMESPACE_DNS
    name = f"telegram_user_{telegram_id}"
    return uuid5(namespace, name)

def get_name_from_url(url: str) -> str:
    """
    Получает название предмета из URL + убирает лишние символы.
    """
    return unquote(urlparse(url).path.split('/')[-1])

def get_listing_id_from_url(url: str) -> int:
    """
    Получает ID предмета из URL.
    """
    return int(urlparse(url).path.split('/')[-2])
