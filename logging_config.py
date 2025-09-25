"""
Конфигурация логирования для Steam Watchlist API

Этот файл содержит настройки логирования, которые можно использовать
для более гибкого управления уровнями логирования в разных средах.
"""

import logging
import sys
from pathlib import Path

def setup_logging(log_level: str = "INFO", log_file: str = None):
    """
    Настройка системы логирования
    
    Args:
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Путь к файлу для записи логов (опционально)
    """
    
    # Создаем директорию для логов если она не существует
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Настройка форматирования
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Настройка обработчиков
    handlers = []
    
    # Консольный обработчик
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)
    
    # Файловый обработчик (если указан файл)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Основная конфигурация логирования
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        handlers=handlers,
        force=True  # Перезаписывает существующую конфигурацию
    )
    
    # Настройка логгера для uvicorn (чтобы не спамил)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    
    return logging.getLogger("steam_api")

# Предустановленные конфигурации для разных сред
DEVELOPMENT_CONFIG = {
    "log_level": "DEBUG",
    "log_file": "/home/amazko/steam/logs/api_dev.log"
}

PRODUCTION_CONFIG = {
    "log_level": "INFO", 
    "log_file": "/home/amazko/steam/logs/api_prod.log"
}

TESTING_CONFIG = {
    "log_level": "WARNING",
    "log_file": None  # Только в консоль при тестировании
}
