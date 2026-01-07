"""Telegram Sender Module for Timetable Telegram Notifier."""

import logging
import os
from typing import Optional

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


def send_telegram_message(
    message: str,
    bot_token: Optional[str] = None,
    chat_id: Optional[str] = None
) -> bool:
    """
    Send a message via Telegram Bot API.
    
    Uses environment variables if token/chat_id not provided:
    - TELEGRAM_BOT_TOKEN
    - TELEGRAM_CHAT_ID
    
    Args:
        message: The message text to send
        bot_token: Telegram bot token (optional, uses env var if not provided)
        chat_id: Telegram chat ID (optional, uses env var if not provided)
    
    Returns:
        True on success, False on failure
        
    Note:
        Logs errors but doesn't raise exceptions to allow continued processing.
    """
    # Get credentials from environment if not provided
    token = bot_token or os.environ.get('TELEGRAM_BOT_TOKEN')
    chat = chat_id or os.environ.get('TELEGRAM_CHAT_ID')
    
    if not token:
        logger.error("Telegram bot token not provided and TELEGRAM_BOT_TOKEN not set")
        return False
    
    if not chat:
        logger.error("Telegram chat ID not provided and TELEGRAM_CHAT_ID not set")
        return False
    
    url = TELEGRAM_API_URL.format(token=token)
    payload = {
        'chat_id': chat,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                logger.info("Message sent successfully")
                return True
            else:
                logger.error(f"Telegram API error: {result.get('description', 'Unknown error')}")
                return False
        else:
            logger.error(f"HTTP error {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error("Request timed out while sending Telegram message")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending message: {e}")
        return False
