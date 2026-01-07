# Timetable Telegram Notifier

Automated class schedule notifications via Telegram, powered by GitHub Actions.

## Features

- Sends notifications 10 min, 5 min, and at class start time
- Runs automatically on GitHub Actions (free!)
- Weekdays only, during class hours
- Timezone-aware (default: IST)
- Smartwatch-friendly compact messages

## Setup

### 1. Fork/Clone this repository

### 2. Get your Telegram Chat ID

1. Create a bot via @BotFather on Telegram
2. Message your bot (send `/start`)
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Find `"chat":{"id":XXXXXXXX}` in the response

### 3. Add GitHub Secrets

Go to your repo → Settings → Secrets and variables → Actions → New repository secret

Add these secrets:
- `TELEGRAM_BOT_TOKEN`: Your bot token from BotFather
- `TELEGRAM_CHAT_ID`: Your chat ID

### 4. Update your timetable

Edit `Timetable_2026.csv` with your schedule.

### 5. Push to GitHub

The workflow runs automatically every 5 minutes on weekdays during class hours.

## Manual Testing

Trigger manually: Actions → Test Notification → Run workflow

## Timezone

Default: `Asia/Kolkata` (IST). Change in `.github/workflows/notify.yml` if needed.
