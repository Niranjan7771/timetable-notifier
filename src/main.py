"""Main Entry Point for Timetable Telegram Notifier."""

import logging
import os
import sys
from pathlib import Path

from src.parser import parse_timetable
from src.matcher import get_pending_notifications
from src.formatter import format_notification
from src.sender import send_telegram_message
from src.discord_sender import send_discord_message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default timezone (Indian Standard Time)
DEFAULT_TIMEZONE = "Asia/Kolkata"


def main():
    """
    Main entry point for the notifier.
    
    1. Parse timetable CSV
    2. Get current time in configured timezone
    3. Find classes needing notifications
    4. Format and send messages
    5. Exit with appropriate code
    """
    # Get configuration from environment
    timezone = os.environ.get('TIMEZONE', DEFAULT_TIMEZONE)
    
    # Find timetable CSV - check multiple locations
    csv_paths = [
        Path('Timetable_2026.csv'),
        Path('timetable.csv'),
        Path(__file__).parent.parent / 'Timetable_2026.csv',
    ]
    
    csv_path = None
    for path in csv_paths:
        if path.exists():
            csv_path = path
            break
    
    if csv_path is None:
        logger.error("Timetable CSV not found. Checked: %s", [str(p) for p in csv_paths])
        sys.exit(1)
    
    logger.info(f"Using timetable: {csv_path}")
    
    # Parse timetable
    try:
        classes = parse_timetable(str(csv_path))
        logger.info(f"Parsed {len(classes)} class slots from timetable")
    except FileNotFoundError:
        logger.error(f"Timetable file not found: {csv_path}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Error parsing timetable: {e}")
        sys.exit(1)
    
    # Get pending notifications
    pending = get_pending_notifications(classes, timezone=timezone)
    
    if not pending:
        logger.info("No notifications to send at this time")
        sys.exit(0)
    
    logger.info(f"Found {len(pending)} notification(s) to send")
    
    # Send each notification
    success_count = 0
    for notification in pending:
        message = format_notification(notification)
        logger.info(f"Sending notification for: {notification.class_slot.class_name}")
        
        # Send to Telegram
        if send_telegram_message(message):
            success_count += 1
        else:
            logger.warning(f"Failed to send Telegram notification for: {notification.class_slot.class_name}")
        
        # Send to Discord
        if send_discord_message(message):
            logger.info(f"Discord notification sent for: {notification.class_slot.class_name}")
        else:
            logger.warning(f"Failed to send Discord notification for: {notification.class_slot.class_name}")
    
    logger.info(f"Sent {success_count}/{len(pending)} notifications successfully")
    
    # Exit with success even if some messages failed
    # (we don't want to fail the workflow for partial failures)
    sys.exit(0)


if __name__ == '__main__':
    main()
