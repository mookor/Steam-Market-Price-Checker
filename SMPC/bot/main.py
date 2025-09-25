"""
Главный файл Steam Monitor Bot
"""
import logging
from telegram import BotCommand
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    ConversationHandler, CallbackQueryHandler, filters
)

from SMPC.bot.config import BotConfig, BotConstants
from SMPC.bot.services import APIService, PriceService, NotificationService
from SMPC.bot.handlers.commands import (
    StartCommandHandler, HelpCommandHandler, PricesCommandHandler,
    SubscribeCommandHandler, UnsubscribeCommandHandler, CurrencySelectionHandler,
    ChangeCurrencyCommandHandler, CurrencyChangeWarningHandler, CurrencyChangeHandler,
    WatchlistPriceUpdateHandler
)
from SMPC.bot.handlers.conversations import AddItemConversationHandler

logger = logging.getLogger(__name__)


class SteamMonitorBot:
    """Главный класс Steam Monitor Bot"""
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.app = Application.builder().token(config.token).build()
        
        # Инициализация сервисов
        self.api_service = APIService()
        self.price_service = PriceService(config)
        self.notification_service = NotificationService(self.app.bot)
        
        # Инициализация обработчиков
        self._init_handlers()
        
        logger.info("Steam Monitor Bot initialized successfully")
    
    def _init_handlers(self):
        """Инициализация всех обработчиков"""
        logger.info("Setting up bot handlers")
        
        try:
            # Создаем экземпляры обработчиков команд
            start_handler = StartCommandHandler(self.api_service, self.price_service, self.notification_service)
            help_handler = HelpCommandHandler(self.api_service, self.price_service, self.notification_service)
            prices_handler = PricesCommandHandler(self.api_service, self.price_service, self.notification_service)
            subscribe_handler = SubscribeCommandHandler(self.api_service, self.price_service, self.notification_service)
            unsubscribe_handler = UnsubscribeCommandHandler(self.api_service, self.price_service, self.notification_service)
            change_currency_handler = ChangeCurrencyCommandHandler(self.api_service, self.price_service, self.notification_service)
            
            # Создаем обработчики валюты
            currency_handler = CurrencySelectionHandler(self.api_service, self.price_service, self.notification_service)
            currency_warning_handler = CurrencyChangeWarningHandler(self.api_service, self.price_service, self.notification_service)
            currency_change_handler = CurrencyChangeHandler(self.api_service, self.price_service, self.notification_service)
            price_update_handler = WatchlistPriceUpdateHandler(self.api_service, self.price_service, self.notification_service)
            
            # Создаем обработчик диалога добавления предмета
            add_item_handler = AddItemConversationHandler(
                self.api_service, 
                self.price_service
            )
            
            # Настраиваем ConversationHandler для добавления предметов
            add_item_conversation = ConversationHandler(
                entry_points=[CommandHandler("add", add_item_handler.handle)],
                states={
                    BotConstants.ITEM_URL: [
                        MessageHandler(filters.TEXT & ~filters.COMMAND, add_item_handler.handle_url)
                    ],
                    BotConstants.ITEM_SELL_PRICE: [
                        MessageHandler(filters.TEXT & ~filters.COMMAND, add_item_handler.handle_sell_price)
                    ],
                    BotConstants.ITEM_BUY_PRICE: [
                        MessageHandler(filters.TEXT & ~filters.COMMAND, add_item_handler.handle_buy_price)
                    ]
                },
                fallbacks=[
                    CommandHandler("cancel", add_item_handler.cancel),
                    CommandHandler("start", self._cancel_and_start),
                    CommandHandler("prices", self._cancel_and_prices),
                    CommandHandler("help", self._cancel_and_help),
                    CommandHandler("add", add_item_handler.handle),
                    CommandHandler("subscribe", self._cancel_and_subscribe),
                    CommandHandler("unsubscribe", self._cancel_and_unsubscribe),
                    CommandHandler("change_currency", self._cancel_and_change_currency)
                ]
            )
            
            # Добавляем обработчики в приложение
            self.app.add_handler(add_item_conversation)
            self.app.add_handler(CommandHandler("start", start_handler.handle))
            self.app.add_handler(CommandHandler("help", help_handler.handle))
            self.app.add_handler(CommandHandler("prices", prices_handler.handle))
            self.app.add_handler(CommandHandler("subscribe", subscribe_handler.handle))
            self.app.add_handler(CommandHandler("unsubscribe", unsubscribe_handler.handle))
            self.app.add_handler(CommandHandler("change_currency", change_currency_handler.handle))
            
            # Добавляем обработчики callback'ов
            self.app.add_handler(CallbackQueryHandler(
                currency_handler.handle_currency_callback, 
                pattern="^currency_(USD|RUB)$"
            ))
            self.app.add_handler(CallbackQueryHandler(
                currency_warning_handler.handle_warning_callback, 
                pattern="^currency_change_(confirm_|cancel)"
            ))
            self.app.add_handler(CallbackQueryHandler(
                currency_change_handler.handle_direct_change_callback, 
                pattern="^currency_direct_change_"
            ))
            self.app.add_handler(CallbackQueryHandler(
                price_update_handler.handle_skip_callback, 
                pattern="^price_update_skip_"
            ))
            
            # Добавляем обработчик текстовых сообщений для обновления цен
            self.app.add_handler(MessageHandler(
                filters.TEXT & ~filters.COMMAND & filters.Regex(r'^\d+\.?\d*\s+\d+\.?\d*$'),
                price_update_handler.handle_price_input
            ))
            
            logger.info("All handlers set up successfully")
            
        except Exception as e:
            logger.error(f"Error setting up handlers: {e}")
            raise
    
    async def _cancel_and_start(self, update, context):
        """Отменить текущий разговор и выполнить команду start"""
        user = update.effective_user
        logger.info(f"Cancelling conversation and executing start for user {user.id}")
        context.user_data.clear()
        await update.message.reply_text(BotConstants.MESSAGES['OPERATION_CANCELLED'])
        
        start_handler = StartCommandHandler(self.api_service, self.price_service, self.notification_service)
        await start_handler.handle(update, context)
        return ConversationHandler.END
    
    async def _cancel_and_prices(self, update, context):
        """Отменить текущий разговор и выполнить команду prices"""
        user = update.effective_user
        logger.info(f"Cancelling conversation and executing prices for user {user.id}")
        context.user_data.clear()
        await update.message.reply_text(BotConstants.MESSAGES['OPERATION_CANCELLED'])
        
        prices_handler = PricesCommandHandler(self.api_service, self.price_service, self.notification_service)
        await prices_handler.handle(update, context)
        return ConversationHandler.END
    
    async def _cancel_and_help(self, update, context):
        """Отменить текущий разговор и выполнить команду help"""
        user = update.effective_user
        logger.info(f"Cancelling conversation and executing help for user {user.id}")
        context.user_data.clear()
        await update.message.reply_text(BotConstants.MESSAGES['OPERATION_CANCELLED'])
        
        help_handler = HelpCommandHandler(self.api_service, self.price_service, self.notification_service)
        await help_handler.handle(update, context)
        return ConversationHandler.END
    
    async def _cancel_and_subscribe(self, update, context):
        """Отменить текущий разговор и выполнить команду subscribe"""
        user = update.effective_user
        logger.info(f"Cancelling conversation and executing subscribe for user {user.id}")
        context.user_data.clear()
        await update.message.reply_text(BotConstants.MESSAGES['OPERATION_CANCELLED'])
        
        subscribe_handler = SubscribeCommandHandler(self.api_service, self.price_service, self.notification_service)
        await subscribe_handler.handle(update, context)
        return ConversationHandler.END
    
    async def _cancel_and_unsubscribe(self, update, context):
        """Отменить текущий разговор и выполнить команду unsubscribe"""
        user = update.effective_user
        logger.info(f"Cancelling conversation and executing unsubscribe for user {user.id}")
        context.user_data.clear()
        await update.message.reply_text(BotConstants.MESSAGES['OPERATION_CANCELLED'])
        
        unsubscribe_handler = UnsubscribeCommandHandler(self.api_service, self.price_service, self.notification_service)
        await unsubscribe_handler.handle(update, context)
        return ConversationHandler.END
    
    async def _cancel_and_change_currency(self, update, context):
        """Отменить текущий разговор и выполнить команду change_currency"""
        user = update.effective_user
        logger.info(f"Cancelling conversation and executing change_currency for user {user.id}")
        context.user_data.clear()
        await update.message.reply_text(BotConstants.MESSAGES['OPERATION_CANCELLED'])
        
        change_currency_handler = ChangeCurrencyCommandHandler(self.api_service, self.price_service, self.notification_service)
        await change_currency_handler.handle(update, context)
        return ConversationHandler.END
    
    async def _update_all_items_price(self, context):
        """Обновить цены всех предметов"""
        logger.info("Starting price update job")
        try:
            items = await self.api_service.get_all_items()
            logger.info(f"Updating prices for {len(items)} items")
            await self.price_service.update_all_prices(self.api_service, items)
            logger.info("Price update job completed successfully")
        except Exception as e:
            logger.error(f"Error in price update job: {e}")
    
    async def _notify_subscribers(self, context):
        """Уведомить подписчиков"""
        logger.info("Starting notification job")
        try:
            await self.notification_service.notify_subscribers(self.api_service)
            logger.info("Notification job completed successfully")
        except Exception as e:
            logger.error(f"Error in notification job: {e}")
    
    def _create_bot_commands(self):
        """Создать меню команд для бота"""
        logger.info("Creating bot commands menu")
        try:
            commands = [
                BotCommand(command, description) 
                for command, description in BotConstants.COMMANDS
            ]
            logger.info(f"Created {len(commands)} bot commands")
            return commands
        except Exception as e:
            logger.error(f"Error creating bot commands menu: {e}")
            return []
    
    async def _setup_bot_commands(self, application):
        """Настроить команды бота"""
        try:
            commands = self._create_bot_commands()
            await application.bot.set_my_commands(commands)
            logger.info("Bot commands menu set successfully")
        except Exception as e:
            logger.error(f"Error setting bot commands: {e}")
    
    def run(self):
        """Запустить бота"""
        logger.info("Starting Steam Monitor Bot")
        try:
            # Настраиваем команды бота
            self.app.post_init = self._setup_bot_commands
            
            # Запускаем периодические задачи
            self.app.job_queue.run_repeating(
                self._update_all_items_price, 
                interval=self.config.update_interval
            )
            self.app.job_queue.run_repeating(
                self._notify_subscribers, 
                interval=self.config.notify_interval
            )
            
            logger.info("Bot handlers configured, starting polling")
            self.app.run_polling()
            
        except Exception as e:
            logger.error(f"Error running bot: {e}")
            raise


def create_bot() -> SteamMonitorBot:
    """Создать экземпляр бота с конфигурацией из переменных окружения"""
    config = BotConfig.from_env()
    return SteamMonitorBot(config)


def main():
    """Главная функция для запуска бота"""
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('bot.log'),
            logging.StreamHandler()
        ]
    )
    
    logger.info("Creating bot instance")
    bot = create_bot()
    logger.info("Starting bot execution")
    bot.run()


if __name__ == "__main__":
    main()
