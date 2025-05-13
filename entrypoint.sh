#!/bin/sh
set -e

# If there's no DB file yet, initialize it
if [ ! -f bookings.db ]; then
  echo "❯ Initializing SQLite schema…"
  python db.py
fi

# If you set INIT_SHEETS=1 in env, run init_sheet() once
if [ "$INIT_SHEETS" = "1" ]; then
  echo "❯ Initializing Google Sheet headers…"
  python - << 'EOF'
from sheets import init_sheet
init_sheet()
EOF
  # Unset so we don't re-run on every restart
  unset INIT_SHEETS
fi

# Finally, start the bot
echo "❯ Starting BookingSaver bot…"
exec python bot.py
