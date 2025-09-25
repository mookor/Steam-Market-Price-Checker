"""
Сервис для отправки уведомлений
"""
import logging
import asyncio
from typing import List, Dict, Any

from telegram import Bot
from SMPC.bot.config import BotConstants
from SMPC.bot.utils.formatters import format_alerts_message

logger = logging.getLogger(__name__)


class NotificationService:
    """Сервис для отправки уведомлений пользователям"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
    
    async def notify_subscribers(self, api_service) -> None:
        """Уведомить всех подписчиков о сработавших алертах"""
        logger.info("Starting notification process")
        
        try:
            subscribers = await api_service.get_subscribers()
            logger.info(f"Found {len(subscribers)} subscribers")
            
            for subscriber in subscribers:
                try:
                    await self._notify_user(subscriber, api_service)
                    # Небольшая задержка между уведомлениями
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"Error notifying subscriber {subscriber.get('telegram_id')}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in notification process: {e}")
    
    async def _notify_user(self, subscriber: Dict[str, Any], api_service) -> None:
        """Уведомить конкретного пользователя"""
        user_id = subscriber['id']
        telegram_id = subscriber['telegram_id']
        currency = subscriber['currency']
        try:
            price_alerts = await api_service.get_watchlist_alerts(user_id, currency)
            print(123, price_alerts)
            # Формируем сообщения для разных типов алертов
            message_parts = []
            
            if price_alerts.get('buy'):
                buy_message = format_alerts_message(
                    price_alerts['buy'], 
                    "💰 Buy alerts:", 
                    "{:.2f} <= {:.2f}",
                    currency
                )
                message_parts.append(buy_message)
            
            if price_alerts.get('sell'):
                sell_message = format_alerts_message(
                    price_alerts['sell'], 
                    "📈 Sell alerts:", 
                    "{:.2f} >= {:.2f}",
                    currency
                )
                message_parts.append(sell_message)
            
            # Отправляем сообщение, если есть алерты
            if message_parts:
                full_message = "\n\n".join(message_parts)
                await self.bot.send_message(
                    telegram_id, 
                    full_message, 
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
                logger.info(f"Successfully notified subscriber {telegram_id}")
            else:
                logger.debug(f"No alerts for subscriber {telegram_id}")
                
        except Exception as e:
            logger.error(f"Error notifying user {telegram_id}: {e}")
            raise
