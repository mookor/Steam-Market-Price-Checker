"""
Сервис для работы с API
"""
import logging
from typing import Dict, Any, List, Optional
from uuid import UUID
from httpx import HTTPStatusError

from SMPC.api import SteamWatchlistAPIClient
from SMPC.bot.config import BotConstants

logger = logging.getLogger(__name__)


class APIService:
    """Сервис для работы с API Steam Watchlist"""
    
    def __init__(self):
        self.client = SteamWatchlistAPIClient()
    
    async def create_user(self, user_uuid: UUID, telegram_id: int, currency: str = "USD") -> bool:
        """Создать или обновить пользователя"""
        try:
            await self.client.create_user(
                id=user_uuid, 
                telegram_id=telegram_id, 
                subscriber=True,
                currency=currency
            )
            logger.info(f"Successfully created/updated user {user_uuid} with currency {currency}")
            return True
        except HTTPStatusError as e:
            logger.error(f"HTTP error creating user {user_uuid}: {e.response.status_code}")
            return e.response.status_code == 500  # Пользователь уже существует
        except Exception as e:
            logger.error(f"Unexpected error creating user {user_uuid}: {e}")
            return False
    
    async def check_user_exists(self, user_uuid: UUID) -> bool:
        """Проверить существование пользователя"""
        try:
            await self.client.get_user(user_uuid)
            logger.info(f"User {user_uuid} exists")
            return True
        except HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.info(f"User {user_uuid} does not exist")
                return False
            logger.error(f"HTTP error checking user {user_uuid}: {e.response.status_code}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking user {user_uuid}: {e}")
            return False
    
    async def get_watchlist(self, user_uuid: UUID) -> List[Dict[str, Any]]:
        """Получить список отслеживания пользователя"""
        try:
            watchlist = await self.client.get_watchlist(user_uuid)
            logger.info(f"Retrieved {len(watchlist)} items from watchlist for user {user_uuid}")
            return watchlist
        except Exception as e:
            logger.error(f"Error getting watchlist for user {user_uuid}: {e}")
            raise
    
    async def check_item_exists(self, item_name: str) -> Dict[str, Any]:
        """Проверить существование предмета"""
        try:
            return await self.client.check_item_exists(item_name)
        except Exception as e:
            logger.error(f"Error checking item existence for {item_name}: {e}")
            raise
    
    async def create_item(self, listing_id: str, name: str, current_price_rub: float, current_price_usd: float, url: str) -> Optional[str]:
        """Создать новый предмет"""
        try:
            item = await self.client.create_item(
                listing_id=listing_id,
                name=name,
                current_price_rub=current_price_rub,
                current_price_usd=current_price_usd,
                url=url
            )
            logger.info(f"Successfully created item {name} with ID: {item['item_id']}")
            return item['item_id']
        except HTTPStatusError as e:
            logger.error(f"HTTP error creating item {name}: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating item {name}: {e}")
            return None
    
    async def add_to_watchlist(
        self, 
        user_id: UUID, 
        item_id: UUID, 
        buy_target_price: float, 
        sell_target_price: float, 
        url: str
    ) -> str:
        """Добавить предмет в список отслеживания"""
        try:
            result = await self.client.add_to_watchlist(
                user_id=user_id,
                item_id=item_id,
                buy_target_price=buy_target_price,
                sell_target_price=sell_target_price,
                url=url
            )
            logger.info(f"Successfully added item {item_id} to watchlist for user {user_id}")
            return result['message']
        except HTTPStatusError as e:
            logger.error(f"HTTP error adding item {item_id} to watchlist: {e.response.status_code}")
            if e.response.status_code == 500:
                return BotConstants.MESSAGES['ITEM_EXISTS']
            else:
                return BotConstants.MESSAGES['SOMETHING_WRONG']
        except Exception as e:
            logger.error(f"Unexpected error adding item {item_id} to watchlist: {e}")
            return BotConstants.MESSAGES['SOMETHING_WRONG']
    
    async def check_item_in_watchlist(self, user_id: UUID, item_id: UUID) -> Dict[str, Any]:
        """Проверить, есть ли предмет в списке отслеживания"""
        try:
            return await self.client.check_item_in_watchlist(user_id, item_id)
        except Exception as e:
            logger.error(f"Error checking item in watchlist: {e}")
            raise
    
    async def change_user_subscription(self, user_id: UUID, subscriber: bool) -> bool:
        """Изменить подписку пользователя"""
        try:
            await self.client.change_user_subscription(user_id=user_id, subscriber=subscriber)
            logger.info(f"Successfully changed subscription for user {user_id} to {subscriber}")
            return True
        except Exception as e:
            logger.error(f"Error changing subscription for user {user_id}: {e}")
            return False
    
    async def get_all_items(self) -> List[Dict[str, Any]]:
        """Получить все предметы"""
        try:
            return await self.client.get_all_items()
        except Exception as e:
            logger.error(f"Error getting all items: {e}")
            raise
    
    async def update_item_price(self, item_name: str, current_price_rub: float, current_price_usd: float) -> bool:
        """Обновить цену предмета"""
        try:
            await self.client.update_item_price(name = item_name, new_price_rub=current_price_rub, new_price_usd=current_price_usd)
            return True
        except Exception as e:
            logger.error(f"Error updating price for item {item_name}: {e}")
            return False
    
    async def get_subscribers(self) -> List[Dict[str, Any]]:
        """Получить всех подписчиков"""
        try:
            return await self.client.get_subscribers()
        except Exception as e:
            logger.error(f"Error getting subscribers: {e}")
            raise
    
    async def get_watchlist_alerts(self, user_id: UUID, currency: str = "USD") -> Dict[str, List[Dict[str, Any]]]:
        """Получить алерты для пользователя"""
        try:
            return await self.client.get_watchlist_alerts(user_id, currency)
        except Exception as e:
            logger.error(f"Error getting watchlist alerts for user {user_id}: {e}")
            raise

    async def change_user_currency(self, user_id: UUID, currency: str) -> bool:
        """Изменить валюту пользователя"""
        try:
            await self.client.change_user_currency(user_id=user_id, currency=currency)
            logger.info(f"Successfully changed currency for user {user_id} to {currency}")
            return True
        except Exception as e:
            logger.error(f"Error changing currency for user {user_id}: {e}")
            return False

    async def update_watchlist_item_prices(self, user_id, watchlist_id, buy_target_price: float, sell_target_price: float) -> bool:
        """Обновить цены покупки и продажи для элемента watchlist"""
        try:
            # Конвертируем в UUID если это строка
            if isinstance(user_id, str):
                from uuid import UUID
                user_id = UUID(user_id)
            if isinstance(watchlist_id, str):
                from uuid import UUID
                watchlist_id = UUID(watchlist_id)
                
            await self.client.update_watchlist_item_prices(
                user_id=user_id,
                watchlist_id=watchlist_id,
                buy_target_price=buy_target_price,
                sell_target_price=sell_target_price
            )
            logger.info(f"Successfully updated watchlist item prices for user {user_id}, watchlist_id {watchlist_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating watchlist item prices for user {user_id}: {e}")
            return False
