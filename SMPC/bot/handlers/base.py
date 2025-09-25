"""
Базовый класс для обработчиков команд
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict
from uuid import UUID

from telegram import Update
from telegram.ext import ContextTypes

from SMPC.bot.utils import telegram_id_to_uuid
from SMPC.bot.config import BotConstants
from SMPC.bot.utils.formatters import format_error_message

logger = logging.getLogger(__name__)


class BaseHandler(ABC):
    """Базовый класс для всех обработчиков команд"""
    
    def __init__(self, api_service, price_service=None, notification_service=None):
        self.api_service = api_service
        self.price_service = price_service
        self.notification_service = notification_service
    
    def _get_user_uuid(self, user) -> UUID:
        """Получить UUID пользователя из Telegram user объекта"""
        try:
            user_uuid = telegram_id_to_uuid(user.id)
            logger.debug(f"Generated UUID {user_uuid} for user {user.id}")
            return user_uuid
        except Exception as e:
            logger.error(f"Error generating UUID for user {user.id}: {e}")
            raise
    
    async def _handle_error(self, update: Update, error: Exception, error_type: str = "server_error") -> None:
        """Обработка ошибок"""
        user = update.effective_user
        logger.error(f"Error in handler for user {user.id}: {error}")
        
        try:
            error_message = format_error_message(error_type)
            await update.message.reply_text(error_message)
        except Exception as e:
            logger.error(f"Error sending error message to user {user.id}: {e}")
    
    @abstractmethod
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Any:
        """Основной метод обработки команды"""
        pass
