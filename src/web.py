"""Simple web server for cron-job.org to trigger notifications."""

import os
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler

from src.parser import parse_timetable
from src.matcher import get_pending_notifications
from src.formatter import format_notification
from src.sender import send_telegram_message
from src.discord_sender import send_discord_message

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TIMEZONE = os.environ.get('TIMEZONE', 'Asia/Kolkata')


def run_notifier():
    """Run the notification logic."""
    try:
        classes = parse_timetable('Timetable_2026.csv')
        pending = get_pending_notifications(classes, timezone=TIMEZONE)
        
        if not pending:
            return "No notifications needed"
        
        results = []
        for notification in pending:
            message = format_notification(notification)
            tg_ok = send_telegram_message(message)
            dc_ok = send_discord_message(message)
            results.append(f"{notification.class_slot.class_name}: TG={tg_ok}, DC={dc_ok}")
        
        return f"Sent {len(pending)} notifications: " + "; ".join(results)
    except Exception as e:
        logger.error(f"Error: {e}")
        return f"Error: {e}"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/notify' or self.path == '/':
            result = run_notifier()
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(result.encode())
            logger.info(f"Request handled: {result}")
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        logger.info("%s - %s" % (self.address_string(), format % args))


def main():
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), Handler)
    logger.info(f"Server running on port {port}")
    server.serve_forever()


if __name__ == '__main__':
    main()
