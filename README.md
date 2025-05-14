# BookingSaver – Telegram → Booking.com → Sheets

BookingSaver is a Telegram bot that:
- Watches a Telegram group for Booking.com links
- Uses Selenium to scrape hotel data from Booking.com
- Fetches Google Maps reviews and ratings for properties
- Stores all data in SQLite
- Mirrors every new hotel listing to a Google Sheet with formatted columns

## 🔧 Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
# Then edit with your real secrets
```

| Variable | Purpose |
|----------|---------|
| `TELEGRAM_BOT_TOKEN` | Bot token from [@BotFather](https://t.me/BotFather) |
| `GOOGLE_CREDENTIALS_JSON` | *Literal* JSON of your Google Service Account key **or** path to the file |
| `SHEET_ID` | Target Google Sheet ID (the hash in its URL) |
| `CHROME_BINARY` | (Optional) Path to Chrome binary (default: `/usr/bin/chromium`) |
| `CHROMEDRIVER_PATH` | (Optional) Path to ChromeDriver (default: `/usr/bin/chromedriver`) |

## 🚀 Setup & Running

### Prerequisites

1. **Telegram Bot**: Create a bot with [@BotFather](https://t.me/BotFather) and get a token
   - Enable bot access to group messages: turn off privacy mode with `/setprivacy` command
   - Add the bot to your Telegram group(s)

2. **Google Sheet**: 
   - Create a Google Sheet to store hotel data
   - Create a Google Service Account with the following permissions:
     - Google Sheets API: `https://www.googleapis.com/auth/spreadsheets`
   - Share your Google Sheet with the service account email as an Editor
   - Get the Sheet ID from its URL: `https://docs.google.com/spreadsheets/d/[SHEET_ID]/edit`

### Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/BookingSaver.git
cd BookingSaver

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize the database
python db.py

# 5. Initialize Google Sheet headers (first run only)
python -c "from sheets import init_sheet; init_sheet()"

# 6. Start the bot
python bot.py
```

### Docker Setup

```bash
# Build and run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f
```

The Docker setup:
- Automatically initializes the database if it doesn't exist
- Sets up Google Sheet headers on first run (via INIT_SHEETS=1)
- Persists data with a named volume

## 📱 Usage

1. Add the bot to your Telegram group
2. Post any Booking.com hotel URL
3. The bot will reply with "Saved ✅" when processing is complete
4. Check your Google Sheet for the new entry with formatting

Example:
```
https://www.booking.com/hotel/pl/krakow-center-apartments.en-gb.html
```

## 🔎 Features

- Extracts hotel data: name, address, price, dates, reviews
- Fetches Google Maps reviews and combines them with Booking.com scores
- Calculates "Overall Score" using weighted averages
- Adds conditional formatting in Google Sheets for easy visual assessment
- Detects duplicate listings (same hotel with same dates)
- Hyperlinks hotel names for quick access to original listings

## ⚠️ Troubleshooting

- **Selenium Issues**: Make sure Chrome and ChromeDriver are installed and paths are correctly set
- **Google API Errors**: Verify your service account has the correct permissions and is shared on the Sheet
- **Bot Not Responding**: Check that privacy mode is disabled for the bot to see group messages

### Common Permissions Issues

- Google Sheets API must be enabled in the Google Cloud Console for your project
- Service account needs Editor access to the specific Sheet
- Your bot needs its privacy mode disabled to see group messages

## 🔧 Technical Details

- Built with Python 3.10+
- Uses Selenium with headless Chrome for robust scraping
- Google Sheets API for formatted data presentation
- SQLite for local data persistence
