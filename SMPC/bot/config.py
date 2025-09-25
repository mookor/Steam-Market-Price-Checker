"""
Конфигурация и константы для бота
"""
import os
from dataclasses import dataclass
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


@dataclass
class BotConfig:
    """Конфигурация бота"""
    token: str
    update_interval: int = 120  # секунды
    notify_interval: int = 180   # секунды
    max_retries: int = 3
    request_timeout: int = 30
    
    @classmethod
    def from_env(cls) -> 'BotConfig':
        """Создать конфигурацию из переменных окружения"""
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
        
        return cls(
            token=token,
            update_interval=int(os.getenv("UPDATE_INTERVAL", "160")),
            notify_interval=int(os.getenv("NOTIFY_INTERVAL", "180")),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            request_timeout=int(os.getenv("REQUEST_TIMEOUT", "30"))
        )


class BotConstants:
    """Константы бота"""
    
    # Состояния диалогов
    ITEM_URL = 1
    ITEM_SELL_PRICE = 2
    ITEM_BUY_PRICE = 3
    
    # Сообщения
    MESSAGES: Dict[str, str] = {
        'WELCOME': 'Welcome to Steam Price Monitor!',
        'INVALID_URL': 'Invalid URL. Please provide a valid Steam Community Market URL.',
        'INVALID_PRICE': 'Invalid price format. Please enter a valid number.',
        'ITEM_EXISTS': 'This item is already in your watchlist.',
        'SUCCESS_ADDED': 'Item successfully added to your watchlist!',
        'OPERATION_CANCELLED': 'Operation cancelled.',
        'SOMETHING_WRONG': 'Something went wrong, please try again later.',
        'EMPTY_WATCHLIST': 'Your watchlist is empty. Use /add to add items to your watchlist.',
        'SUBSCRIBED': 'You are now subscribed to notifications.',
        'UNSUBSCRIBED': 'You are now unsubscribed from notifications.',
        'BUY_PRICE_TOO_HIGH': 'Buy price must be less than sell price. Please try again.',
        'ENTER_URL': 'Enter the URL of the item you want to add to the watchlist:\nFor example: https://steamcommunity.com/market/listings/730/Fracture%20Case',
        'ENTER_SELL_PRICE': 'Enter the sell price of the item',
        'ENTER_BUY_PRICE': 'Enter the buy price of the item'
    }
    
    # Команды бота
    COMMANDS = [
        ("start", "Запустить бота и показать справку"),
        ("add", "Добавить товар в список отслеживания"),
        ("prices", "Показать текущие цены всех товаров"),
        ("help", "Показать справку по командам"),
        ("cancel", "Отменить текущую операцию"),
        ("subscribe", "Подписаться на уведомления"),
        ("unsubscribe", "Отписаться от уведомлений"),
        ("change_currency", "Сменить валюту (USD/RUB)")
    ]
    
    # Лимиты
    MAX_PRICE = 10000.0
    MIN_PRICE = 0.01
    MAX_ITEMS_PER_USER = 50
