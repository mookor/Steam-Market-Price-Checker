import httpx
import asyncio
import json
from uuid import UUID
from typing import Optional, List, Dict, Any


class SteamWatchlistAPIClient:
    """Клиент для работы с Steam Watchlist API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient()
    
    async def close(self):
        """Закрыть соединение"""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    # Методы для работы с пользователями
    async def create_user(self, id: UUID, telegram_id: int, subscriber: bool = True, currency: str = "USD") -> Dict[str, Any]:
        """Создать нового пользователя"""
        data = {"id": str(id), "telegram_id": telegram_id, "subscriber": subscriber, "currency": currency}
        
        response = await self.client.post(f"{self.base_url}/users/", json=data)
        response.raise_for_status()
        return response.json()
    
    async def get_user(self, user_id: UUID) -> Dict[str, Any]:
        """Получить пользователя по ID"""
        response = await self.client.get(f"{self.base_url}/users/{user_id}")
        response.raise_for_status()
        return response.json()
    
    async def get_subscribers(self) -> List[Dict[str, Any]]:
        """Получить список всех пользователей-подписчиков"""
        response = await self.client.get(f"{self.base_url}/users/subscribers")
        response.raise_for_status()
        return response.json()
    
    # Методы для работы с товарами
    async def create_item(self, listing_id: int, name: str, current_price_usd: float, current_price_rub: float, url: str) -> Dict[str, Any]:
        """Создать товар или получить существующий"""
        data = {
            "listing_id": str(listing_id),
            "name": name,
            "current_price_usd": current_price_usd,
            "current_price_rub": current_price_rub,
            "url": url
        }
        response = await self.client.post(f"{self.base_url}/items/", json=data)
        response.raise_for_status()
        return response.json()
    
    async def get_item(self, item_id: UUID) -> Dict[str, Any]:
        """Получить товар по ID"""
        response = await self.client.get(f"{self.base_url}/items/{item_id}")
        response.raise_for_status()
        return response.json()
    
    async def update_item_price(self, name: str, new_price_usd: float, new_price_rub: float) -> Dict[str, Any]:
        """Обновить цены товара по имени"""
        data = {"name": name, "new_price_usd": new_price_usd, "new_price_rub": new_price_rub}
        response = await self.client.put(f"{self.base_url}/items/price", json=data)
        response.raise_for_status()
        return response.json()
    
    async def check_item_exists(self, item_name: str) -> Dict[str, Any]:
        """Проверить существование товара по имени"""
        response = await self.client.get(f"{self.base_url}/items/exists/{item_name}")
        response.raise_for_status()
        return response.json()
    
    async def add_to_watchlist(self, user_id: UUID, item_id: UUID, 
                              buy_target_price: float, sell_target_price: float, url: str) -> Dict[str, Any]:
        """Добавить товар в watchlist пользователя"""
        data = {
            "item_id": str(item_id),
            "buy_target_price": buy_target_price,
            "sell_target_price": sell_target_price,
            "url": url
        }
        response = await self.client.post(f"{self.base_url}/users/{user_id}/watchlist", json=data)
        response.raise_for_status()
        return response.json()
    
    async def get_watchlist(self, user_id: UUID) -> List[Dict[str, Any]]:
        """Получить watchlist пользователя"""
        response = await self.client.get(f"{self.base_url}/users/{user_id}/watchlist")
        response.raise_for_status()
        return response.json()
    
    async def remove_from_watchlist(self, user_id: UUID, item_id: UUID) -> Dict[str, Any]:
        """Удалить товар из watchlist пользователя"""
        response = await self.client.delete(f"{self.base_url}/users/{user_id}/watchlist/{item_id}")
        response.raise_for_status()
        return response.json()
    
    async def get_watchlist_alerts(self, user_id: UUID, currency: str = 'usd') -> Dict[str, Any]:
        """Получить алерты по ценам из watchlist пользователя"""
        params = {"currency": currency}
        response = await self.client.get(f"{self.base_url}/users/{user_id}/watchlist/alerts", params=params)
        response.raise_for_status()
        return response.json()
    
    async def check_item_in_watchlist(self, user_id: UUID, item_id: UUID) -> Dict[str, Any]:
        """Проверить, есть ли предмет в watchlist пользователя"""
        response = await self.client.get(f"{self.base_url}/users/{user_id}/watchlist/check/{item_id}")
        response.raise_for_status()
        return response.json()
    
    async def get_all_items(self) -> List[Dict[str, Any]]:
        """Получить все товары"""
        response = await self.client.get(f"{self.base_url}/items/")
        response.raise_for_status()
        return response.json()

    async def change_user_subscription(self, user_id: UUID, subscriber: bool) -> Dict[str, Any]:
        """Изменить статус подписки пользователя"""
        response = await self.client.put(f"{self.base_url}/subscription/{user_id}", json={"subscriber": subscriber})
        response.raise_for_status()
        return response.json()

    async def change_user_currency(self, user_id: UUID, currency: str) -> Dict[str, Any]:
        """Изменить валюту пользователя"""
        response = await self.client.put(f"{self.base_url}/users/{user_id}/currency", json={"currency": currency})
        response.raise_for_status()
        return response.json()

    async def update_watchlist_item_prices(self, user_id: UUID, watchlist_id: UUID, buy_target_price: float, sell_target_price: float) -> Dict[str, Any]:
        """Обновить цены покупки и продажи для элемента watchlist"""
        data = {
            "buy_target_price": buy_target_price,
            "sell_target_price": sell_target_price
        }
        response = await self.client.put(f"{self.base_url}/users/{user_id}/watchlist/{watchlist_id}/prices", json=data)
        response.raise_for_status()
        return response.json()
    
    # Служебные методы
    async def health_check(self) -> Dict[str, Any]:
        """Проверка состояния API"""
        response = await self.client.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()