"""
Сервис для работы с ценами
"""
import logging
import asyncio
from typing import Optional

from SMPC.price_parser import PriceParser, Currency
from SMPC.bot.config import BotConfig

logger = logging.getLogger(__name__)


class PriceService:
    """Сервис для парсинга и обновления цен"""
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.price_parser = PriceParser()
    
    async def parse_price(self, name: str, listing_id: str) -> Optional[float]:
        """Парсить цену предмета"""
        try:
            logger.info(f"Parsing price for item: {name}")
            current_price = await self.price_parser.parse_dual_currency_with_retries(
                name=name, 
                listing_id=listing_id
            )
            logger.info(f"Successfully parsed price for {name}: ${current_price}")
            return {'rub': round(float(current_price['rub']), 2), 'usd': round(float(current_price['usd']), 2)}
        except Exception as e:
            logger.error(f"Error parsing price for {name}: {e}")
            return None
    
    async def update_all_prices(self, api_service, items: list) -> None:
        """Обновить цены всех предметов"""
        logger.info(f"Updating prices for {len(items)} items")
        
        for item in items:
            try:
                current_price = await self.parse_price(
                    name=item['name'], 
                    listing_id=item['listing_id']
                )
                
                if current_price is not None:
                    success = await api_service.update_item_price(item['name'], current_price['rub'], current_price['usd'])
                    if success:
                        logger.info(f"Successfully updated price for {item['name']}: ${current_price}")
                    else:
                        logger.error(f"Failed to update price for {item['name']}")
                else:
                    logger.warning(f"Could not parse price for {item['name']}")
                
                # Небольшая задержка между запросами
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error updating price for {item['name']}: {e}")
                continue
