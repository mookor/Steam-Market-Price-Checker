import re
import asyncio
import logging
from typing import Dict, Optional, Union, Tuple

import aiohttp
import yaml
from enum import Enum


class Currency(Enum):
    USD = 1
    EUR = 3
    RUB = 5
    KZT = 37

class PriceParser:
    
    def __init__(self,  max_retries: int = 5, request_timeout: int = 10):
        """
        Инициализация парсера цен Steam Market.
        
        Args:
            max_retries: Максимальное количество попыток повтора
            request_timeout: Таймаут для HTTP запросов в секундах
        """
        self.max_retries = max_retries
        self.request_timeout = request_timeout
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('price_parser.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        self.session = None
        self._connector = None
    
    async def _ensure_session(self):
        """Создает aiohttp сессию если она не существует."""
        if self.session is None or self.session.closed:
            self._connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            timeout = aiohttp.ClientTimeout(total=self.request_timeout)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            self.session = aiohttp.ClientSession(
                connector=self._connector,
                timeout=timeout,
                headers=headers
            )

    async def parse_with_retries(self, name: str, listing_id: int = 730, currency: Currency = Currency.RUB) -> Optional[float]:
        """Парсит цену товара с несколькими попытками."""
        for _ in range(self.max_retries):
            price = await self.parse(name, listing_id, currency)
            if price is not None:
                return price
            await asyncio.sleep(1)
        return None

    async def parse_dual_currency_with_retries(self, name: str, listing_id: int = 730) -> Optional[Dict[str, float]]:
        """Парсит цены товара в USD и RUB с несколькими попытками."""
        for _ in range(self.max_retries):
            prices = await self.parse_dual_currency(name, listing_id)
            if prices is not None:
                return prices
            await asyncio.sleep(1)
        return None

    async def parse_dual_currency(self, name: str, listing_id: int = 730) -> Optional[Dict[str, float]]:
        """Парсит цены товара в USD и RUB за один запрос."""
        try:
            await self._ensure_session()
            encoded_name = self.fix_name(name)
            
            # Получение ID товара
            listing_url = f"https://steamcommunity.com/market/listings/{listing_id}/{encoded_name}"
            self.logger.debug(f"Запрос страницы товара: {listing_url}")
            
            async with self.session.get(listing_url) as name_id_response:
                name_id_response.raise_for_status()
                html_text = await name_id_response.text()
            
            # Поиск ID товара в HTML
            match = re.search(r"Market_LoadOrderSpread\(\s*(\d+)\s*\)", html_text)
            if not match:
                self.logger.warning(f"Не найден ID товара для '{name}' на странице")
                return None
                
            name_id = match.group(1)
            self.logger.debug(f"Найден ID товара: {name_id}")
            
            # Небольшая пауза между запросами
            await asyncio.sleep(1)
            
            # Получение цен в обеих валютах
            prices = {}
            
            # Получение цены в USD
            usd_price = await self._get_price_for_currency(name, name_id, Currency.USD)
            if usd_price is not None:
                prices['usd'] = usd_price
            
            # Небольшая пауза между запросами
            await asyncio.sleep(0.5)
            
            # Получение цены в RUB
            rub_price = await self._get_price_for_currency(name, name_id, Currency.RUB)
            if rub_price is not None:
                prices['rub'] = rub_price
            
            if len(prices) == 2:
                self.logger.debug(f"Получены цены для '{name}': USD={prices['usd']}, RUB={prices['rub']}")
                return prices
            else:
                self.logger.warning(f"Не удалось получить цены в обеих валютах для '{name}'")
                return None
                
        except asyncio.TimeoutError:
            self.logger.error(f"Таймаут запроса для '{name}'")
            return None
        except aiohttp.ClientConnectionError:
            self.logger.error(f"Ошибка соединения для '{name}'")
            return None
        except aiohttp.ClientResponseError as e:
            self.logger.error(f"HTTP ошибка для '{name}': {e}")
            return None
        except aiohttp.ClientError as e:
            self.logger.error(f"Ошибка клиента для '{name}': {e}")
            return None
        except Exception as e:
            self.logger.error(f"Неожиданная ошибка при парсинге '{name}': {e}")
            return None

    async def _get_price_for_currency(self, name: str, name_id: str, currency: Currency) -> Optional[float]:
        """Получает цену товара для конкретной валюты."""
        try:
            # Получение данных о ценах
            price_url = (f"https://steamcommunity.com/market/itemordershistogram"
                        f"?country=US&language=russian&currency={currency.value}&item_nameid={name_id}&two_factor=0")
            
            self.logger.debug(f"Запрос данных о ценах в {currency.name}: {price_url}")
            
            async with self.session.get(price_url) as response:
                response.raise_for_status()
                
                try:
                    data = await response.json()
                except aiohttp.ContentTypeError as e:
                    self.logger.error(f"Не удалось декодировать JSON ответ для '{name}' в {currency.name}: {e}")
                    return None
            
            # Проверка наличия данных о цене
            if "lowest_sell_order" not in data:
                self.logger.warning(f"Отсутствует информация о минимальной цене для '{name}' в {currency.name}")
                return None
                
            if data["lowest_sell_order"] is None:
                self.logger.warning(f"Минимальная цена для '{name}' в {currency.name} равна null")
                return None
            
            try:
                lowest_sell_order = int(data["lowest_sell_order"])
                price = lowest_sell_order / 100
                self.logger.debug(f"Получена цена для '{name}' в {currency.name}: {price}")
                return price
                
            except (ValueError, TypeError) as e:
                self.logger.error(f"Не удалось преобразовать цену для '{name}' в {currency.name}: {data['lowest_sell_order']}, ошибка: {e}")
                return None
                
        except Exception as e:
            self.logger.error(f"Ошибка при получении цены для '{name}' в {currency.name}: {e}")
            return None
    
    async def parse(self, name: str, listing_id: int = 730, currency: Currency = Currency.RUB) -> Optional[float]:
        """Парсит цену товара с одной попытки в указанной валюте."""
        try:
            await self._ensure_session()
            encoded_name = self.fix_name(name)
            
            # Получение ID товара
            listing_url = f"https://steamcommunity.com/market/listings/{listing_id}/{encoded_name}"
            self.logger.debug(f"Запрос страницы товара: {listing_url}")
            
            async with self.session.get(listing_url) as name_id_response:
                name_id_response.raise_for_status()
                html_text = await name_id_response.text()
            
            # Поиск ID товара в HTML
            match = re.search(r"Market_LoadOrderSpread\(\s*(\d+)\s*\)", html_text)
            if not match:
                self.logger.warning(f"Не найден ID товара для '{name}' на странице")
                return None
                
            name_id = match.group(1)
            self.logger.debug(f"Найден ID товара: {name_id}")
            
            # Небольшая пауза между запросами
            await asyncio.sleep(1)
            
            # Получение цены в указанной валюте
            return await self._get_price_for_currency(name, name_id, currency)
                
        except asyncio.TimeoutError:
            self.logger.error(f"Таймаут запроса для '{name}'")
            return None
        except aiohttp.ClientConnectionError:
            self.logger.error(f"Ошибка соединения для '{name}'")
            return None
        except aiohttp.ClientResponseError as e:
            self.logger.error(f"HTTP ошибка для '{name}': {e}")
            return None
        except aiohttp.ClientError as e:
            self.logger.error(f"Ошибка клиента для '{name}': {e}")
            return None
        except Exception as e:
            self.logger.error(f"Неожиданная ошибка при парсинге '{name}': {e}")
            return None

    def fix_name(self, name: str) -> str:
        """Кодирует название товара для URL."""
        if not isinstance(name, str):
            raise ValueError("Название должно быть строкой")
        
        import urllib.parse
        return urllib.parse.quote(name.strip())
    
    async def close(self):
        """Закрывает сессию."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.logger.info("Сессия закрыта")
        if self._connector:
            await self._connector.close()
    
    async def __aenter__(self):
        """Поддержка асинхронного контекстного менеджера."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Автоматическое закрытие сессии."""
        await self.close()
