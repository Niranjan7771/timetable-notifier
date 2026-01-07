"""Time Matcher Module for Timetable Telegram Notifier."""

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from enum import Enum
from typing import List

import pytz

from src.parser import ClassSlot


class NotificationType(Enum):
    """Types of notifications based on time before class."""
    TEN_MINUTES = 10
    FIVE_MINUTES = 5
    AT_TIME = 0


@dataclass
class PendingNotification:
    """Represents a notification that needs to be sent."""
    class_slot: ClassSlot
    notification_type: NotificationType


# Map day names to weekday numbers (Monday=0, Sunday=6)
DAY_MAP = {
    'MONDAY': 0,
    'TUESDAY': 1,
    'WEDNESDAY': 2,
    'THURSDAY': 3,
    'FRIDAY': 4,
    'SATURDAY': 5,
    'SUNDAY': 6
}


def is_weekday(dt: datetime) -> bool:
    """Return True if datetime is Monday-Friday (weekday 0-4)."""
    return dt.weekday() < 5


def get_day_name(dt: datetime) -> str:
    """Get the day name (MONDAY, TUESDAY, etc.) from a datetime."""
    days = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY']
    return days[dt.weekday()]


def is_within_notification_window(
    class_start: time,
    current_dt: datetime,
    window_minutes: int,
    tolerance_minutes: int = 2
) -> bool:
    """
    Check if class_start is within window_minutes of current time.
    
    Uses a tolerance to account for GitHub Actions timing variance.
    For example, with window=10 and tolerance=2, matches if class starts
    in 8-12 minutes from now.
    
    Args:
        class_start: The class start time
        current_dt: Current datetime (timezone-aware)
        window_minutes: Target minutes before class (10, 5, or 0)
        tolerance_minutes: Allowed variance (default 2 minutes)
    
    Returns:
        True if within the notification window
    """
    # Create datetime for class start on the same day
    class_dt = current_dt.replace(
        hour=class_start.hour,
        minute=class_start.minute,
        second=0,
        microsecond=0
    )
    
    # Calculate minutes until class
    diff = class_dt - current_dt
    minutes_until = diff.total_seconds() / 60
    
    # Check if within tolerance of target window
    lower_bound = window_minutes - tolerance_minutes
    upper_bound = window_minutes + tolerance_minutes
    
    return lower_bound <= minutes_until <= upper_bound


def get_pending_notifications(
    classes: List[ClassSlot],
    current_time: datetime = None,
    timezone: str = "Asia/Kolkata"
) -> List[PendingNotification]:
    """
    Check all classes and return those needing notifications.
    
    Matches classes starting in exactly 10, 5, or 0 minutes (with tolerance).
    Returns empty list on weekends.
    
    Args:
        classes: List of ClassSlot objects from the timetable
        current_time: Current datetime (if None, uses now in specified timezone)
        timezone: Timezone string (default: Asia/Kolkata for IST)
    
    Returns:
        List of PendingNotification objects for classes needing alerts
    """
    # Get current time in specified timezone
    tz = pytz.timezone(timezone)
    if current_time is None:
        current_dt = datetime.now(tz)
    else:
        # Ensure timezone awareness
        if current_time.tzinfo is None:
            current_dt = tz.localize(current_time)
        else:
            current_dt = current_time.astimezone(tz)
    
    # Skip weekends
    if not is_weekday(current_dt):
        return []
    
    # Get current day name
    current_day = get_day_name(current_dt)
    
    # Filter classes for today
    today_classes = [c for c in classes if c.day == current_day]
    
    pending: List[PendingNotification] = []
    
    # Check each notification window
    notification_windows = [
        (NotificationType.TEN_MINUTES, 10),
        (NotificationType.FIVE_MINUTES, 5),
        (NotificationType.AT_TIME, 0),
    ]
    
    for class_slot in today_classes:
        for notif_type, window_minutes in notification_windows:
            if is_within_notification_window(
                class_slot.start_time,
                current_dt,
                window_minutes
            ):
                pending.append(PendingNotification(
                    class_slot=class_slot,
                    notification_type=notif_type
                ))
                break  # Only one notification per class per run
    
    return pending
