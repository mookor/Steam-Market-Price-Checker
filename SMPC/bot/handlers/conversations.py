"""
Обработчики диалогов (conversations) бота
"""
import logging
from uuid import UUID
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from SMPC.bot.handlers.base import BaseHandler
from SMPC.bot.config import BotConstants
from SMPC.bot.utils.validators import validate_steam_url, validate_price, validate_price_range
from SMPC.bot.utils.formatters import format_error_message
from SMPC.bot.utils import get_name_from_url, get_listing_id_from_url

logger = logging.getLogger(__name__)


class AddItemConversationHandler(BaseHandler):
    """Обработчик диалога добавления предмета"""
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Начало диалога добавления предмета"""
        user = update.effective_user
        context.user_data['user_id'] = self._get_user_uuid(update.effective_user)
        
        db_user = await self.api_service.client.get_user(context.user_data['user_id'])
        print(123, db_user)
        context.user_data['currency'] = db_user['currency']
        
        logger.info(f"Add item flow started by user {user.id} (@{user.username})")
        
        try:
            await update.message.reply_text(
                BotConstants.MESSAGES['ENTER_URL'], 
                disable_web_page_preview=True
            )
            logger.info(f"Add item start message sent to user {user.id}")
            return BotConstants.ITEM_URL
        except Exception as e:
            logger.error(f"Error in add item start for user {user.id}: {e}")
            context.user_data.clear()
            return ConversationHandler.END
    
    async def handle_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка URL предмета"""
        user = update.effective_user
        url = update.message.text.strip()
        
        logger.info(f"User {user.id} entered URL: {url}")
        
        if not validate_steam_url(url):
            logger.warning(f"Invalid URL entered by user {user.id}: {url}")
            await update.message.reply_text(format_error_message('validation'))
            return BotConstants.ITEM_URL
        
        try:
            context.user_data['url'] = url
            context.user_data['listing_id'] = get_listing_id_from_url(url)
            context.user_data['item_name'] = get_name_from_url(url)
            logger.info(f"Parsed item data for user {user.id}: listing_id={context.user_data['listing_id']}, name={context.user_data['item_name']}")
            
            item_id = await self._get_or_create_item_id(context)
            logger.info(f"Got/created item ID {item_id} for user {user.id}")
            
            context.user_data['item_id'] = item_id
            
            # Проверяем, есть ли уже предмет в списке отслеживания
            in_watchlist = await self.api_service.check_item_in_watchlist(
                context.user_data['user_id'], 
                item_id
            )
            if in_watchlist['in_watchlist']:
                logger.info(f"Item {item_id} already in watchlist for user {user.id}")
                await update.message.reply_text(format_error_message('item_exists'))
                context.user_data.clear()
                return ConversationHandler.END
            
            await update.message.reply_text(BotConstants.MESSAGES['ENTER_SELL_PRICE'] + f" in ({context.user_data['currency']})")
            logger.info(f"Requesting sell price from user {user.id}")
            return BotConstants.ITEM_SELL_PRICE
            
        except Exception as e:
            logger.error(f"Error processing URL for user {user.id}: {e}")
            await update.message.reply_text(format_error_message('server_error'))
            context.user_data.clear()
            return ConversationHandler.END
    
    async def handle_sell_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка цены продажи"""
        user = update.effective_user
        price = update.message.text.strip()
        logger.info(f"User {user.id} entered sell price: {price}")
        
        if not validate_price(price):
            logger.warning(f"Invalid sell price entered by user {user.id}: {price}")
            await update.message.reply_text(format_error_message('price_validation'))
            return BotConstants.ITEM_SELL_PRICE
        
        context.user_data['sell_price'] = price
        logger.info(f"Sell price {price} saved for user {user.id}")
        
        try:
            await update.message.reply_text(BotConstants.MESSAGES['ENTER_BUY_PRICE'] + f" in ({context.user_data['currency']})")
            logger.info(f"Requesting buy price from user {user.id}")
            return BotConstants.ITEM_BUY_PRICE
        except Exception as e:
            logger.error(f"Error requesting buy price from user {user.id}: {e}")
            context.user_data.clear()
            return ConversationHandler.END
    
    async def handle_buy_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка цены покупки"""
        user = update.effective_user
        price = update.message.text.strip()
        logger.info(f"User {user.id} entered buy price: {price}")
        
        if not validate_price(price):
            logger.warning(f"Invalid buy price entered by user {user.id}: {price}")
            await update.message.reply_text(format_error_message('price_validation'))
            return BotConstants.ITEM_BUY_PRICE
        
        context.user_data['buy_price'] = price
        logger.info(f"Buy price {price} saved for user {user.id}")
        
        try:
            buy_price = float(context.user_data['buy_price'])
            sell_price = float(context.user_data['sell_price'])
            
            if not validate_price_range(buy_price, sell_price):
                await update.message.reply_text(format_error_message('price_range'))
                return BotConstants.ITEM_SELL_PRICE
            
            logger.info(f"Adding item to watchlist for user {user.id}")
            message = await self._add_item_to_watchlist(context)
            await update.message.reply_text(message)
            logger.info(f"Item successfully added to watchlist for user {user.id}")
            
        except Exception as e:
            logger.error(f"Error adding item to watchlist for user {user.id}: {e}")
            await update.message.reply_text(format_error_message('server_error'))
        finally:
            context.user_data.clear()
            logger.info(f"Cleared user data for user {user.id}")
        
        return ConversationHandler.END
    
    async def _get_or_create_item_id(self, context: ContextTypes.DEFAULT_TYPE) -> UUID:
        """Получить ID предмета из базы данных или создать новый"""
        item_name = context.user_data['item_name']
        logger.info(f"Checking if item exists: {item_name}")
        
        try:
            item = await self.api_service.check_item_exists(item_name)
            
            if item['exists']:
                logger.info(f"Item {item_name} already exists with ID: {item['item_id']}")
                return UUID(item['item_id'])
            
            # Если предмет не существует, создаем новый
            logger.info(f"Item {item_name} doesn't exist, creating new item")
            logger.info(f"Parsing current price for item: {item_name}")
            
            current_price = await self.price_service.parse_price(
                name=context.user_data['item_name'], 
                listing_id=context.user_data['listing_id']
            )
            
            if current_price is None:
                raise Exception("Failed to parse current price")
            
            context.user_data['current_price_rub'] = current_price['rub']
            context.user_data['current_price_usd'] = current_price['usd']
            logger.info(f"Current price parsed for {item_name}: ${current_price}")
            
            item_id = await self._add_item_to_database(context)
            if not item_id:
                logger.error(f"Failed to create item {item_name} in database")
                raise Exception("Failed to create item in database")
            
            logger.info(f"Successfully created item {item_name} with ID: {item_id}")
            return UUID(item_id)
            
        except Exception as e:
            logger.error(f"Error in _get_or_create_item_id for item {item_name}: {e}")
            raise
    
    async def _add_item_to_watchlist(self, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Добавить предмет в список отслеживания"""
        user_id = context.user_data['user_id']
        item_id = context.user_data['item_id']
        buy_price = round(float(context.user_data['buy_price']), 2)
        sell_price = round(float(context.user_data['sell_price']), 2)
        url = context.user_data['url']
        
        logger.info(f"Adding item {item_id} to watchlist for user {user_id} with buy_price=${buy_price}, sell_price=${sell_price}, url={url}")
        
        return await self.api_service.add_to_watchlist(
            user_id=user_id,
            item_id=item_id,
            buy_target_price=buy_price,
            sell_target_price=sell_price,
            url=url
        )
    
    async def _add_item_to_database(self, context: ContextTypes.DEFAULT_TYPE) -> str:
        """Добавить предмет в базу данных"""
        item_name = context.user_data['item_name']
        listing_id = context.user_data['listing_id']
        current_price_rub = round(float(context.user_data['current_price_rub']), 2)
        current_price_usd = round(float(context.user_data['current_price_usd']), 2)
        url = context.user_data['url']
        
        logger.info(f"Creating item in database: {item_name} (listing_id: {listing_id}, price: ${current_price_rub}, ${current_price_usd})")
        
        return await self.api_service.create_item(
            listing_id=listing_id,
            name=item_name,
            current_price_rub=current_price_rub,
            current_price_usd=current_price_usd,
            url=url
        )
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Отмена диалога"""
        user = update.effective_user
        logger.info(f"Add item flow cancelled by user {user.id} (@{user.username})")
        
        try:
            await update.message.reply_text(BotConstants.MESSAGES['OPERATION_CANCELLED'])
            context.user_data.clear()
            logger.info(f"User data cleared for cancelled operation by user {user.id}")
            return ConversationHandler.END
        except Exception as e:
            logger.error(f"Error in cancel operation for user {user.id}: {e}")
            return ConversationHandler.END
