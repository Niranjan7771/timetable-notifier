"""Google Calendar Sync Module for Timetable."""

import os
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.parser import parse_timetable, ClassSlot

# If modifying these scopes, delete the token.pickle file
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Day name to weekday number mapping (Monday=0)
DAY_TO_WEEKDAY = {
    'MONDAY': 0,
    'TUESDAY': 1,
    'WEDNESDAY': 2,
    'THURSDAY': 3,
    'FRIDAY': 4,
    'SATURDAY': 5,
    'SUNDAY': 6
}


def get_calendar_service():
    """
    Authenticate and return Google Calendar service.
    
    First run will open browser for OAuth consent.
    Subsequent runs use saved token.
    """
    creds = None
    token_path = Path('token.pickle')
    credentials_path = Path('credentials.json')
    
    # Load existing token
    if token_path.exists():
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    
    # Refresh or get new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not credentials_path.exists():
                raise FileNotFoundError(
                    "credentials.json not found!\n"
                    "Please download OAuth credentials from Google Cloud Console:\n"
                    "1. Go to https://console.cloud.google.com/\n"
                    "2. Create/select a project\n"
                    "3. Enable Google Calendar API\n"
                    "4. Create OAuth 2.0 credentials (Desktop app)\n"
                    "5. Download and save as 'credentials.json'"
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path), SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Save token for future runs
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    
    return build('calendar', 'v3', credentials=creds)


def get_next_weekday(weekday: int, start_date: datetime) -> datetime:
    """Get the next occurrence of a weekday from start_date."""
    days_ahead = weekday - start_date.weekday()
    if days_ahead < 0:  # Target day already happened this week
        days_ahead += 7
    return start_date + timedelta(days=days_ahead)


def create_calendar_event(
    service,
    class_slot: ClassSlot,
    event_date: datetime,
    timezone: str = 'Asia/Kolkata'
) -> dict:
    """Create a single calendar event for a class slot."""
    
    # Combine date with class times
    start_datetime = datetime.combine(
        event_date.date(),
        class_slot.start_time
    )
    end_datetime = datetime.combine(
        event_date.date(),
        class_slot.end_time
    )
    
    # Build event title with details
    title = class_slot.class_name
    if class_slot.details:
        title = f"{title} ({class_slot.details})"
    
    # Build description
    description = f"Location: {class_slot.location}" if class_slot.location else ""
    if class_slot.details:
        description += f"\nType: {class_slot.details}"
    
    event = {
        'summary': title,
        'location': class_slot.location,
        'description': description,
        'start': {
            'dateTime': start_datetime.isoformat(),
            'timeZone': timezone,
        },
        'end': {
            'dateTime': end_datetime.isoformat(),
            'timeZone': timezone,
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': 15},
            ],
        },
    }
    
    return event


def sync_timetable_to_calendar(
    csv_path: str,
    weeks: int = 16,
    start_date: Optional[datetime] = None,
    calendar_id: str = 'primary',
    timezone: str = 'Asia/Kolkata'
) -> dict:
    """
    Sync timetable to Google Calendar.
    
    Args:
        csv_path: Path to timetable CSV
        weeks: Number of weeks to create events for (default: 16 for a semester)
        start_date: Start date for events (default: next Monday)
        calendar_id: Google Calendar ID (default: primary)
        timezone: Timezone for events
        
    Returns:
        Dict with created/failed event counts
    """
    # Parse timetable
    classes = parse_timetable(csv_path)
    print(f"Parsed {len(classes)} class slots from timetable")
    
    # Get calendar service
    service = get_calendar_service()
    
    # Default start date to next Monday
    if start_date is None:
        today = datetime.now()
        start_date = get_next_weekday(0, today)  # Next Monday
    
    print(f"Creating events starting from: {start_date.strftime('%Y-%m-%d')}")
    print(f"Duration: {weeks} weeks")
    
    created = 0
    failed = 0
    
    for week in range(weeks):
        week_start = start_date + timedelta(weeks=week)
        
        for class_slot in classes:
            weekday = DAY_TO_WEEKDAY.get(class_slot.day)
            if weekday is None:
                continue
            
            event_date = get_next_weekday(weekday, week_start)
            
            # Skip if event_date is before week_start (shouldn't happen but safety check)
            if event_date < week_start:
                event_date += timedelta(weeks=1)
            
            event = create_calendar_event(service, class_slot, event_date, timezone)
            
            try:
                service.events().insert(
                    calendarId=calendar_id,
                    body=event
                ).execute()
                created += 1
                print(f"  ✓ {class_slot.class_name} - {event_date.strftime('%a %d %b')}")
            except HttpError as e:
                failed += 1
                print(f"  ✗ Failed: {class_slot.class_name} - {e}")
    
    return {'created': created, 'failed': failed}


def sync_single_week(
    csv_path: str,
    week_start: datetime,
    calendar_id: str = 'primary',
    timezone: str = 'Asia/Kolkata'
) -> dict:
    """Sync timetable for a single week only."""
    return sync_timetable_to_calendar(
        csv_path=csv_path,
        weeks=1,
        start_date=week_start,
        calendar_id=calendar_id,
        timezone=timezone
    )


def list_calendars():
    """List all available calendars for the authenticated user."""
    service = get_calendar_service()
    calendars = service.calendarList().list().execute()
    
    print("\nAvailable Calendars:")
    print("-" * 50)
    for cal in calendars.get('items', []):
        print(f"  {cal['summary']}")
        print(f"    ID: {cal['id']}")
        print()
    
    return calendars


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Sync timetable to Google Calendar')
    parser.add_argument(
        '--csv', 
        default='Timetable_2026.csv',
        help='Path to timetable CSV file'
    )
    parser.add_argument(
        '--weeks',
        type=int,
        default=16,
        help='Number of weeks to create events for (default: 16)'
    )
    parser.add_argument(
        '--start-date',
        help='Start date in YYYY-MM-DD format (default: next Monday)'
    )
    parser.add_argument(
        '--calendar-id',
        default='primary',
        help='Google Calendar ID (default: primary)'
    )
    parser.add_argument(
        '--timezone',
        default='Asia/Kolkata',
        help='Timezone (default: Asia/Kolkata)'
    )
    parser.add_argument(
        '--list-calendars',
        action='store_true',
        help='List available calendars and exit'
    )
    
    args = parser.parse_args()
    
    if args.list_calendars:
        list_calendars()
    else:
        start = None
        if args.start_date:
            start = datetime.strptime(args.start_date, '%Y-%m-%d')
        
        result = sync_timetable_to_calendar(
            csv_path=args.csv,
            weeks=args.weeks,
            start_date=start,
            calendar_id=args.calendar_id,
            timezone=args.timezone
        )
        
        print(f"\n{'='*50}")
        print(f"Sync Complete!")
        print(f"  Created: {result['created']} events")
        print(f"  Failed: {result['failed']} events")
