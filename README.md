# Timetable Telegram Notifier

Automated class schedule notifications via Telegram, powered by GitHub Actions.

## Features

- 📚 Sends notifications 10 min, 5 min, and at class start time
- 🤖 Runs automatically on GitHub Actions (free!)
- 📅 Weekdays only, during class hours
- 🕐 Timezone-aware (default: IST)

## Setup

### 1. Fork/Clone this repository

### 2. Get your Telegram Chat ID

1. Message your bot on Telegram (send `/start`)
2. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Find `"chat":{"id":XXXXXXXX}` in the response

### 3. Add GitHub Secrets

Go to your repo → Settings → Secrets and variables → Actions → New repository secret

Add these secrets:
- `TELEGRAM_BOT_TOKEN`: Your bot token (e.g., `8244228005:AAFXJxGEsxaf9VGy3qsnTJ4A4lXL7YrcBXI`)
- `TELEGRAM_CHAT_ID`: Your chat ID (e.g., `799065584`)

### 4. Update your timetable

Edit `Timetable_2026.csv` with your schedule. Format:
```csv
Day,8:00 - 8:50,9:00 - 9:50,...
MONDAY,Class Name (Room, Code),Another Class (Room),...
```

### 5. Push to GitHub

The workflow runs automatically every 5 minutes on weekdays during class hours.

## Manual Testing

Trigger manually: Actions → Timetable Notifier → Run workflow

## Local Testing

```bash
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"
python -m src.main
```

## Timezone

Default: `Asia/Kolkata` (IST). Change in `.github/workflows/notify.yml` if needed.
# timetable-notifier
