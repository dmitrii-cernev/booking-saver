# BookingSaver – Telegram → Booking.com → Sheets

BookingSaver watches a Telegram group for Booking.com links, reverse‑engineers
Booking.com’s **GraphQL** calls, extracts key hotel data, stores it in
**SQLite**, and mirrors every new row to a public **Google Sheet**.

> **Tech stack**  
> Python 3.10+, `python-telegram-bot >=20`, `requests`, `graphql-core`,
> `google-api-python-client`, `oauth2client`, SQLite (`sqlite3` std‑lib).

---

## 🔧 Environment variables (`.env` or real shell env)

| Variable | Purpose |
|----------|---------|
| `TELEGRAM_BOT_TOKEN`   | Bot token from @BotFather |
| `GOOGLE_CREDENTIALS_JSON` | *Literal* JSON of your Google SA key **or** path to the file |
| `SHEET_ID`             | Target Google Sheet ID (the hash in its URL) |

Create a `.env` from the sample:

```bash
cp .env.example .env
# then edit with your real secrets
```
## 🚀Setup

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python3 db.py   # one‑off DB initialisation
python3 bot.py  # the bot is now polling
```
Add the bot to your Telegram group (it must see messages).
Post any Booking.com URL; within seconds a row appears both in bookings.db
and in your Google Sheet.

## 🧪 Quick test

https://www.booking.com/hotel/pl/krakow-center-apartments.en-gb.html
The bot replies with a short “Saved ✅” and you should see something like:

hotel_id	name	city	country	checkin	price	currency	scraped_at


## ⚠️ Reverse‑engineering note

Booking.com’s public web uses an internal GraphQL gateway (/graphql) to load
accommodation data 
Medium
.
If Booking change field names or headers, tweak scraper.py::_graphql_payload
accordingly (dev‑tools → Network → “graphql?op=AccommodationAvailability”).
