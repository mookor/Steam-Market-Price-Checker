#!/usr/bin/env python3
"""
Пример запуска модульного Steam Monitor Bot
"""
import os
import sys
import logging
from pathlib import Path


from SMPC.bot.main import create_bot

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
    
    logger = logging.getLogger(__name__)
    
    # Проверяем наличие токена
    if not os.getenv("TELEGRAM_BOT_TOKEN"):
        logger.error("TELEGRAM_BOT_TOKEN environment variable is required")
        logger.info("Please set your bot token in .env file or environment variables")
        logger.info("Example: export TELEGRAM_BOT_TOKEN='your_token_here'")
        sys.exit(1)
    
    try:
        logger.info("Creating modular Steam Monitor Bot")
        bot = create_bot()
        logger.info("Starting bot execution")
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
