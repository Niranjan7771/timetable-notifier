"""CSV Parser Module for Timetable Telegram Notifier."""

import csv
import re
from dataclasses import dataclass
from datetime import time
from typing import List, Optional, Tuple


@dataclass
class ClassSlot:
    """Represents a single class slot in the timetable."""
    day: str  # MONDAY, TUESDAY, etc.
    start_time: time
    end_time: time
    class_name: str
    location: str
    details: Optional[str] = None  # Lab, Tutorial, etc.


def parse_time_slot(time_str: str, is_afternoon: bool = False) -> Tuple[time, time]:
    """
    Parse a time slot string like '8:00 - 8:50' into start and end times.
    
    Args:
        time_str: Time slot string in format "H:MM - H:MM"
        is_afternoon: If True, converts hours 1-6 to 13-18 (PM)
    
    Returns:
        Tuple of (start_time, end_time)
    """
    parts = time_str.split(' - ')
    if len(parts) != 2:
        raise ValueError(f"Invalid time slot format: {time_str}")
    
    def parse_single_time(t: str, afternoon: bool) -> time:
        t = t.strip()
        hour, minute = map(int, t.split(':'))
        # Convert to 24-hour format for afternoon slots
        if afternoon and 1 <= hour <= 6:
            hour += 12
        return time(hour=hour, minute=minute)
    
    start = parse_single_time(parts[0], is_afternoon)
    end = parse_single_time(parts[1], is_afternoon)
    return start, end


def parse_class_entry(entry: str) -> Tuple[str, str, Optional[str]]:
    """
    Parse a class entry like 'Deep Learning (H15, F)' or 'Deep Learning (Lab, L509, J3/X3)'.
    
    Returns:
        Tuple of (class_name, location, details)
        - details is None for regular classes
        - details contains "Lab", "Tutorial", etc. for special sessions
    """
    entry = entry.strip()
    
    if not entry or entry.upper() in ('LUNCH', 'FREE'):
        return entry, '', None
    
    # Match pattern: "Class Name (location info)"
    match = re.match(r'^(.+?)\s*\((.+)\)$', entry)
    if not match:
        return entry, '', None
    
    class_name = match.group(1).strip()
    location_info = match.group(2).strip()
    
    # Check for special session types (Lab, Tut, Tutorial)
    details = None
    location = location_info
    
    # Pattern for Lab/Tutorial entries: "Lab, L509, J3/X3" or "Tut, H14, X4"
    special_match = re.match(r'^(Lab|Tut|Tutorial),?\s*(.+)$', location_info, re.IGNORECASE)
    if special_match:
        details = special_match.group(1)
        location = special_match.group(2).strip()
    
    return class_name, location, details


def parse_timetable(csv_path: str) -> List[ClassSlot]:
    """
    Parse the CSV timetable and return a list of ClassSlot objects.
    
    Handles both morning (8:00-1:50) and afternoon (2:00-5:50) sections.
    Skips empty slots, LUNCH, and Free entries.
    
    Args:
        csv_path: Path to the CSV file
        
    Returns:
        List of ClassSlot objects
        
    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If CSV format is invalid
    """
    slots: List[ClassSlot] = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    if not rows:
        raise ValueError("CSV file is empty")
    
    # Find section boundaries
    morning_start = None
    afternoon_start = None
    
    for i, row in enumerate(rows):
        if row and row[0].upper() == 'DAY':
            if morning_start is None:
                morning_start = i
            else:
                afternoon_start = i
                break
    
    if morning_start is None:
        raise ValueError("Could not find morning section header")
    
    # Parse morning section
    morning_header = rows[morning_start]
    time_slots_morning = morning_header[1:]  # Skip 'Day' column
    
    morning_end = afternoon_start if afternoon_start else len(rows)
    for row in rows[morning_start + 1:morning_end]:
        if not row or not row[0] or row[0].upper() == 'DAY':
            continue
        day = row[0].upper()
        for col_idx, cell in enumerate(row[1:], start=0):
            if col_idx >= len(time_slots_morning):
                break
            cell = cell.strip() if cell else ''
            if not cell or cell.upper() in ('LUNCH', 'FREE', ''):
                continue
            
            time_slot_str = time_slots_morning[col_idx]
            try:
                start_t, end_t = parse_time_slot(time_slot_str, is_afternoon=False)
            except ValueError:
                continue
            
            class_name, location, details = parse_class_entry(cell)
            if class_name and class_name.upper() not in ('LUNCH', 'FREE'):
                slots.append(ClassSlot(
                    day=day,
                    start_time=start_t,
                    end_time=end_t,
                    class_name=class_name,
                    location=location,
                    details=details
                ))
    
    # Parse afternoon section if exists
    if afternoon_start is not None:
        afternoon_header = rows[afternoon_start]
        time_slots_afternoon = [t for t in afternoon_header[1:] if t.strip()]
        
        for row in rows[afternoon_start + 1:]:
            if not row or not row[0]:
                continue
            day = row[0].upper()
            if day == 'DAY':
                continue
            for col_idx, cell in enumerate(row[1:], start=0):
                if col_idx >= len(time_slots_afternoon):
                    break
                cell = cell.strip() if cell else ''
                if not cell or cell.upper() in ('LUNCH', 'FREE', ''):
                    continue
                
                time_slot_str = time_slots_afternoon[col_idx]
                try:
                    start_t, end_t = parse_time_slot(time_slot_str, is_afternoon=True)
                except ValueError:
                    continue
                
                class_name, location, details = parse_class_entry(cell)
                if class_name and class_name.upper() not in ('LUNCH', 'FREE'):
                    slots.append(ClassSlot(
                        day=day,
                        start_time=start_t,
                        end_time=end_t,
                        class_name=class_name,
                        location=location,
                        details=details
                    ))
    
    return slots
