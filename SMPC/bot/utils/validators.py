"""
Валидаторы для бота
"""
import re
from typing import Tuple
from SMPC.bot.config import BotConstants


def validate_steam_url(url: str) -> bool:
    """Валидация URL Steam Community Market"""
    if not url or not isinstance(url, str):
        return False
    
    pattern = r'^https://steamcommunity\.com/market/listings/\d+/[^/]+/?$'
    return bool(re.match(pattern, url.strip()))


def validate_price(price_str: str) -> bool:
    """Валидация формата цены"""
    if not price_str or not isinstance(price_str, str):
        return False
    
    try:
        price = float(price_str.strip())
        return BotConstants.MIN_PRICE <= price <= BotConstants.MAX_PRICE
    except (ValueError, TypeError):
        return False


def validate_price_range(buy_price: float, sell_price: float) -> bool:
    """Валидация диапазона цен"""
    return (BotConstants.MIN_PRICE <= buy_price < sell_price <= BotConstants.MAX_PRICE)


def validate_telegram_id(telegram_id: int) -> bool:
    """Валидация Telegram ID"""
    return isinstance(telegram_id, int) and telegram_id > 0


def validate_item_name(name: str) -> bool:
    """Валидация названия предмета"""
    if not name or not isinstance(name, str):
        return False
    
    # Проверяем, что название не пустое и не слишком длинное
    return 1 <= len(name.strip()) <= 200


def validate_listing_id(listing_id: str) -> bool:
    """Валидация listing ID"""
    if not listing_id or not isinstance(listing_id, str):
        return False
    
    # Проверяем, что это числовая строка
    return listing_id.strip().isdigit() and len(listing_id.strip()) > 0
