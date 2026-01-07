"""Discord Sender Module for Timetable Notifier."""

import logging
import os
from typing import Optional

import requests

logger = logging.getLogger(__name__)


def send_discord_message(
    message: str,
    webhook_url: Optional[str] = None
) -> bool:
    """
    Send a message via Discord Webhook.
    
    Args:
        message: The message text to send
        webhook_url: Discord webhook URL (optional, uses env var if not provided)
    
    Returns:
        True on success, False on failure
    """
    url = webhook_url or os.environ.get('DISCORD_WEBHOOK_URL')
    
    if not url:
        logger.error("Discord webhook URL not provided and DISCORD_WEBHOOK_URL not set")
        return False
    
    payload = {
        'content': message,
        'username': 'Timetable Bot'
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 204:
            logger.info("Discord message sent successfully")
            return True
        else:
            logger.error(f"Discord error {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Discord request error: {e}")
        return False
