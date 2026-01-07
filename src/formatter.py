"""Message Formatter Module for Timetable Telegram Notifier."""

from src.matcher import NotificationType, PendingNotification


def get_notification_prefix(notification_type: NotificationType) -> str:
    """
    Return the appropriate timing text based on notification type.
    """
    if notification_type == NotificationType.TEN_MINUTES:
        return "in 10 min"
    elif notification_type == NotificationType.FIVE_MINUTES:
        return "in 5 min"
    else:  # AT_TIME
        return "NOW"


def format_time_slot(start_time) -> str:
    """Format time for display (12-hour format, compact)."""
    hour = start_time.hour
    minute = start_time.minute
    period = "AM" if hour < 12 else "PM"
    if hour > 12:
        hour -= 12
    elif hour == 0:
        hour = 12
    
    if minute == 0:
        return f"{hour}{period}"
    return f"{hour}:{minute:02d}{period}"


def format_notification(notification: PendingNotification) -> str:
    """
    Format a notification into a compact smartwatch-friendly message.
    No emojis, short and clear.
    
    Example outputs:
    - "Deep Learning in 10 min\nH15 | 9AM"
    - "HCI NOW\nH14 | 10AM"
    - "Deep Learning (Lab) in 5 min\nL509 | 4PM"
    """
    slot = notification.class_slot
    timing = get_notification_prefix(notification.notification_type)
    time_str = format_time_slot(slot.start_time)
    
    # Build class name with details if present
    class_display = slot.class_name
    if slot.details:
        class_display = f"{slot.class_name} ({slot.details})"
    
    # Compact location
    location = slot.location.split(',')[0].strip() if slot.location else "TBA"
    
    # Compose compact message
    return f"{class_display} {timing}\n{location} | {time_str}"
