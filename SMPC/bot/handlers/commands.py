"""
Обработчики команд бота
"""
import logging
from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from SMPC.bot.handlers.base import BaseHandler
from SMPC.bot.config import BotConstants
from SMPC.bot.utils.formatters import format_watchlist, format_help_message

logger = logging.getLogger(__name__)


class StartCommandHandler(BaseHandler):
    """Обработчик команды /start"""
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        logger.info(f"Start command called by user {user.id} (@{user.username})")
        
        try:
            user_uuid = self._get_user_uuid(user)
            logger.info(f"Generated user UUID: {user_uuid} for user {user.id}")
            
            # Проверяем, существует ли пользователь
            user_exists = await self.api_service.check_user_exists(user_uuid)
            
            if user_exists:
                logger.info(f"User {user_uuid} already exists, showing help")
                await self._help_command(update, context)
            else:
                logger.info(f"New user {user_uuid}, showing currency selection")
                # Для нового пользователя показываем выбор валюты
                currency_handler = CurrencySelectionHandler(self.api_service, self.price_service, self.notification_service)
                await currency_handler.handle(update, context)
            
        except Exception as e:
            await self._handle_error(update, e, "server_error")
    
    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показать справку"""
        user = update.effective_user
        logger.info(f"Help command called by user {user.id} (@{user.username})")
        
        try:
            help_text = format_help_message()
            await update.message.reply_text(help_text)
            logger.info(f"Help message sent successfully to user {user.id}")
        except Exception as e:
            logger.error(f"Error sending help message to user {user.id}: {e}")


class HelpCommandHandler(BaseHandler):
    """Обработчик команды /help"""
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await StartCommandHandler._help_command(self, update, context)


class PricesCommandHandler(BaseHandler):
    """Обработчик команды /prices"""
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        logger.info(f"Prices command called by user {user.id} (@{user.username})")
        
        try:
            user_uuid = self._get_user_uuid(user)
            logger.info(f"Getting watchlist for user {user.id} (UUID: {user_uuid})")
            
            watchlist = await self.api_service.get_watchlist(user_uuid)
            logger.info(f"Retrieved {len(watchlist)} items from watchlist for user {user.id}")
            
            db_user = await self.api_service.client.get_user(user_uuid)
            currency = db_user['currency']
            response = format_watchlist(watchlist, currency)
            await update.message.reply_text(response)
            logger.info(f"Prices message sent successfully to user {user.id}")
            
        except Exception as e:
            logger.error(f"Error in prices command for user {user.id}: {e}")
            await self._handle_error(update, e, "server_error")


class SubscribeCommandHandler(BaseHandler):
    """Обработчик команды /subscribe"""
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        user_id = self._get_user_uuid(user)
        logger.info(f"Subscribe command called by user {user.id} (@{user.username})")
        
        try:
            success = await self.api_service.change_user_subscription(user_id=user_id, subscriber=True)
            if success:
                await update.message.reply_text(BotConstants.MESSAGES['SUBSCRIBED'])
                logger.info(f"User {user.id} successfully subscribed")
            else:
                await update.message.reply_text(BotConstants.MESSAGES['SOMETHING_WRONG'])
                logger.error(f"Failed to subscribe user {user.id}")
        except Exception as e:
            await self._handle_error(update, e, "server_error")


class UnsubscribeCommandHandler(BaseHandler):
    """Обработчик команды /unsubscribe"""
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        user_id = self._get_user_uuid(user)
        logger.info(f"Unsubscribe command called by user {user.id} (@{user.username})")
        
        try:
            success = await self.api_service.change_user_subscription(user_id=user_id, subscriber=False)
            if success:
                await update.message.reply_text(BotConstants.MESSAGES['UNSUBSCRIBED'])
                logger.info(f"User {user.id} successfully unsubscribed")
            else:
                await update.message.reply_text(BotConstants.MESSAGES['SOMETHING_WRONG'])
                logger.error(f"Failed to unsubscribe user {user.id}")
        except Exception as e:
            await self._handle_error(update, e, "server_error")


class CurrencySelectionHandler(BaseHandler):
    """Обработчик выбора валюты для новых пользователей"""
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показать выбор валюты новому пользователю"""
        user = update.effective_user
        logger.info(f"Currency selection requested for user {user.id} (@{user.username})")
        
        try:
            # Создаем inline клавиатуру с выбором валюты
            keyboard = [
                [
                    InlineKeyboardButton("USD 💵", callback_data="currency_USD"),
                    InlineKeyboardButton("RUB 💰", callback_data="currency_RUB")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            welcome_text = (
                "Welcome to Steam Price Monitor! 🎮\n\n"
                "Please select your preferred currency for price notifications:"
            )
            
            await update.message.reply_text(welcome_text, reply_markup=reply_markup)
            logger.info(f"Currency selection message sent to user {user.id}")
            
        except Exception as e:
            logger.error(f"Error showing currency selection to user {user.id}: {e}")
            await self._handle_error(update, e, "server_error")
    
    async def handle_currency_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработать выбор валюты"""
        query = update.callback_query
        user = query.from_user
        
        try:
            await query.answer()  # Подтверждаем получение callback
            
            # Извлекаем выбранную валюту из callback_data
            currency = query.data.split("_")[1]  # currency_USD -> USD
            logger.info(f"User {user.id} selected currency: {currency}")
            
            # Создаем пользователя с выбранной валютой
            user_uuid = self._get_user_uuid(user)
            success = await self.api_service.create_user(user_uuid, user.id, currency)
            
            if success:
                logger.info(f"Successfully created user {user_uuid} with currency {currency}")
                
                # Обновляем сообщение
                confirmation_text = (
                    f"Great! Your preferred currency is set to {currency} 💰\n\n"
                    "You can now use the bot to monitor Steam item prices. "
                    "Use /help to see available commands."
                )
                
                await query.edit_message_text(confirmation_text)
                
                # Показываем справку
                help_text = format_help_message()
                await context.bot.send_message(chat_id=user.id, text=help_text)
                
            else:
                logger.error(f"Failed to create user {user_uuid} with currency {currency}")
                await query.edit_message_text(
                    "Sorry, something went wrong during setup. Please try again with /start"
                )
                
        except Exception as e:
            logger.error(f"Error handling currency callback for user {user.id}: {e}")
            await query.edit_message_text(
                "Sorry, something went wrong. Please try again with /start"
            )


class ChangeCurrencyCommandHandler(BaseHandler):
    """Обработчик команды /change_currency"""
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        logger.info(f"Change currency command called by user {user.id} (@{user.username})")
        
        try:
            user_uuid = self._get_user_uuid(user)
            
            # Получаем текущую валюту пользователя
            db_user = await self.api_service.client.get_user(user_uuid)
            current_currency = db_user['currency']
            
            # Получаем watchlist пользователя
            watchlist = await self.api_service.get_watchlist(user_uuid)
            
            if not watchlist:
                # Если watchlist пуст, можно сразу менять валюту
                currency_handler = CurrencyChangeHandler(self.api_service, self.price_service, self.notification_service)
                await currency_handler.show_currency_selection(update, context, current_currency)
            else:
                # Если есть элементы в watchlist, показываем предупреждение
                warning_handler = CurrencyChangeWarningHandler(self.api_service, self.price_service, self.notification_service)
                await warning_handler.show_warning(update, context, current_currency, len(watchlist))
            
        except Exception as e:
            await self._handle_error(update, e, "server_error")


class CurrencyChangeWarningHandler(BaseHandler):
    """Обработчик предупреждения о смене валюты"""
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Основной метод обработки (не используется напрямую)"""
        pass
    
    async def show_warning(self, update: Update, context: ContextTypes.DEFAULT_TYPE, current_currency: str, watchlist_count: int) -> None:
        """Показать предупреждение о смене валюты"""
        user = update.effective_user
        logger.info(f"Showing currency change warning to user {user.id}")
        
        try:
            new_currency = "RUB" if current_currency == "USD" else "USD"
            
            warning_text = (
                f"⚠️ **Currency Change Warning** ⚠️\n\n"
                f"You are about to change your currency from **{current_currency}** to **{new_currency}**.\n\n"
                f"📋 You have **{watchlist_count}** items in your watchlist.\n"
                f"💰 After changing currency, you will need to update the buy and sell target prices "
                f"for each item in your watchlist to match the new currency.\n\n"
                f"Do you want to continue?"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ Yes, continue", callback_data=f"currency_change_confirm_{new_currency}"),
                    InlineKeyboardButton("❌ Cancel", callback_data="currency_change_cancel")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(warning_text, reply_markup=reply_markup, parse_mode='Markdown')
            logger.info(f"Currency change warning sent to user {user.id}")
            
        except Exception as e:
            logger.error(f"Error showing currency change warning to user {user.id}: {e}")
            await self._handle_error(update, e, "server_error")
    
    async def handle_warning_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработать ответ на предупреждение"""
        query = update.callback_query
        user = query.from_user
        
        try:
            await query.answer()
            
            if query.data == "currency_change_cancel":
                await query.edit_message_text("Currency change cancelled. Your current settings remain unchanged.")
                logger.info(f"User {user.id} cancelled currency change")
                return
            
            # Извлекаем новую валюту из callback_data
            new_currency = query.data.split("_")[-1]  # currency_change_confirm_USD -> USD
            logger.info(f"User {user.id} confirmed currency change to {new_currency}")
            
            # Меняем валюту пользователя
            user_uuid = self._get_user_uuid(user)
            success = await self.api_service.change_user_currency(user_uuid, new_currency)
            
            if success:
                await query.edit_message_text(
                    f"✅ Currency successfully changed to {new_currency}!\n\n"
                    f"Now let's update the prices in your watchlist..."
                )
                
                # Запускаем процесс обновления цен в watchlist
                price_update_handler = WatchlistPriceUpdateHandler(self.api_service, self.price_service, self.notification_service)
                await price_update_handler.start_price_updates(query, context, user_uuid, new_currency)
            else:
                await query.edit_message_text(
                    "❌ Sorry, something went wrong while changing your currency. Please try again later."
                )
                
        except Exception as e:
            logger.error(f"Error handling currency change warning callback for user {user.id}: {e}")
            await query.edit_message_text(
                "❌ Sorry, something went wrong. Please try again with /change_currency"
            )


class CurrencyChangeHandler(BaseHandler):
    """Обработчик смены валюты (для пользователей с пустым watchlist)"""
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Основной метод обработки (не используется напрямую)"""
        pass
    
    async def show_currency_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, current_currency: str) -> None:
        """Показать выбор новой валюты"""
        user = update.effective_user
        logger.info(f"Showing currency selection to user {user.id}")
        
        try:
            new_currency = "RUB" if current_currency == "USD" else "USD"
            
            text = (
                f"💱 **Change Currency**\n\n"
                f"Current currency: **{current_currency}**\n"
                f"New currency: **{new_currency}**\n\n"
                f"Since your watchlist is empty, we can change your currency immediately.\n"
                f"Do you want to continue?"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ Yes, change currency", callback_data=f"currency_direct_change_{new_currency}"),
                    InlineKeyboardButton("❌ Cancel", callback_data="currency_change_cancel")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            logger.info(f"Currency selection sent to user {user.id}")
            
        except Exception as e:
            logger.error(f"Error showing currency selection to user {user.id}: {e}")
            await self._handle_error(update, e, "server_error")
    
    async def handle_direct_change_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработать прямую смену валюты"""
        query = update.callback_query
        user = query.from_user
        
        try:
            await query.answer()
            
            if query.data == "currency_change_cancel":
                await query.edit_message_text("Currency change cancelled. Your current settings remain unchanged.")
                logger.info(f"User {user.id} cancelled currency change")
                return
            
            # Извлекаем новую валюту из callback_data
            new_currency = query.data.split("_")[-1]  # currency_direct_change_USD -> USD
            logger.info(f"User {user.id} confirmed direct currency change to {new_currency}")
            
            # Меняем валюту пользователя
            user_uuid = self._get_user_uuid(user)
            success = await self.api_service.change_user_currency(user_uuid, new_currency)
            
            if success:
                await query.edit_message_text(
                    f"✅ Currency successfully changed to {new_currency}!\n\n"
                    f"You can now add items to your watchlist with prices in {new_currency}."
                )
                logger.info(f"Successfully changed currency for user {user.id} to {new_currency}")
            else:
                await query.edit_message_text(
                    "❌ Sorry, something went wrong while changing your currency. Please try again later."
                )
                
        except Exception as e:
            logger.error(f"Error handling direct currency change callback for user {user.id}: {e}")
            await query.edit_message_text(
                "❌ Sorry, something went wrong. Please try again with /change_currency"
            )


class WatchlistPriceUpdateHandler(BaseHandler):
    """Обработчик пошагового обновления цен в watchlist"""
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Основной метод обработки (не используется напрямую)"""
        pass
    
    async def start_price_updates(self, query, context: ContextTypes.DEFAULT_TYPE, user_uuid, new_currency: str) -> None:
        """Начать процесс обновления цен"""
        try:
            # Получаем watchlist пользователя
            watchlist = await self.api_service.get_watchlist(user_uuid)
            
            if not watchlist:
                await context.bot.send_message(
                    chat_id=query.from_user.id,
                    text="✅ Currency changed successfully! Your watchlist is empty, so no price updates are needed."
                )
                return
            
            # Сохраняем данные в context для пошагового обновления
            context.user_data['currency_update'] = {
                'user_uuid': str(user_uuid),
                'new_currency': new_currency,
                'watchlist': watchlist,
                'current_index': 0
            }
            
            # Начинаем с первого элемента
            await self.show_next_item_for_update(query.from_user.id, context)
            
        except Exception as e:
            logger.error(f"Error starting price updates: {e}")
            await context.bot.send_message(
                chat_id=query.from_user.id,
                text="❌ Sorry, something went wrong while preparing price updates. Please try again later."
            )
    
    async def show_next_item_for_update(self, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показать следующий элемент для обновления цены"""
        try:
            update_data = context.user_data.get('currency_update')
            if not update_data:
                return
            
            watchlist = update_data['watchlist']
            current_index = update_data['current_index']
            new_currency = update_data['new_currency']
            
            if current_index >= len(watchlist):
                # Все элементы обновлены
                await context.bot.send_message(
                    chat_id=user_id,
                    text="🎉 All watchlist items have been updated! Your currency change is now complete."
                )
                # Очищаем данные из context
                context.user_data.pop('currency_update', None)
                return
            
            item = watchlist[current_index]
            item_name = item['item']['name']
            # Округляем цены для корректного отображения
            current_buy_price = round(float(item['buy_target_price']), 2)
            current_sell_price = round(float(item['sell_target_price']), 2)
            
            text = (
                f"💰 **Update Prices** ({current_index + 1}/{len(watchlist)})\n\n"
                f"**Item:** {item_name}\n"
                f"**Current buy target:** {current_buy_price:.2f}\n"
                f"**Current sell target:** {current_sell_price:.2f}\n\n"
                f"Please enter new prices for **{new_currency}** in format:\n"
                f"`buy_price sell_price`\n\n"
                f"Example: `25.50 35.00`"
            )
            
            keyboard = [
                [InlineKeyboardButton("⏭️ Skip this item", callback_data=f"price_update_skip_{current_index}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await context.bot.send_message(
                chat_id=user_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error showing next item for update: {e}")
    
    async def handle_price_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработать ввод новых цен"""
        user = update.effective_user
        
        try:
            update_data = context.user_data.get('currency_update')
            if not update_data:
                return
            
            # Парсим введенные цены
            text = update.message.text.strip()
            prices = text.split()
            
            if len(prices) != 2:
                await update.message.reply_text(
                    "❌ Please enter prices in format: `buy_price sell_price`\n"
                    "Example: `25.50 35.00`",
                    parse_mode='Markdown'
                )
                return
            
            try:
                buy_price = float(prices[0])
                sell_price = float(prices[1])
            except ValueError:
                await update.message.reply_text(
                    "❌ Please enter valid numbers for prices.\n"
                    "Example: `25.50 35.00`",
                    parse_mode='Markdown'
                )
                return
            
            if buy_price <= 0 or sell_price <= 0:
                await update.message.reply_text("❌ Prices must be greater than 0.")
                return
            
            if buy_price >= sell_price:
                await update.message.reply_text("❌ Buy price must be less than sell price.")
                return
            
            # Обновляем цены
            watchlist = update_data['watchlist']
            current_index = update_data['current_index']
            user_uuid = update_data['user_uuid']
            
            item = watchlist[current_index]
            watchlist_id = item['id']
            
            success = await self.api_service.update_watchlist_item_prices(
                user_id=user_uuid,
                watchlist_id=watchlist_id,
                buy_target_price=buy_price,
                sell_target_price=sell_price
            )
            
            if success:
                await update.message.reply_text(f"✅ Prices updated for {item['item']['name']}")
                
                # Переходим к следующему элементу
                context.user_data['currency_update']['current_index'] += 1
                await self.show_next_item_for_update(user.id, context)
            else:
                await update.message.reply_text("❌ Failed to update prices. Please try again.")
            
        except Exception as e:
            logger.error(f"Error handling price input for user {user.id}: {e}")
            await update.message.reply_text("❌ Something went wrong. Please try again.")
    
    async def handle_skip_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработать пропуск элемента"""
        query = update.callback_query
        user = query.from_user
        
        try:
            await query.answer()
            
            update_data = context.user_data.get('currency_update')
            if not update_data:
                return
            
            # Переходим к следующему элементу
            context.user_data['currency_update']['current_index'] += 1
            
            await query.edit_message_text("⏭️ Item skipped.")
            await self.show_next_item_for_update(user.id, context)
            
        except Exception as e:
            logger.error(f"Error handling skip callback for user {user.id}: {e}")
