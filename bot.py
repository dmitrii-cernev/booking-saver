"""
BookingSaver Telegram bot.
Listens for Booking.com URLs, scrapes hotel data via internal GraphQL,
persists to SQLite and appends to Google Sheets.
"""

import os
import re
import logging
from datetime import datetime, timezone
from typing import List

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

import scraper
import db
import sheets

from dotenv import load_dotenv
load_dotenv()
# Logging ---------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("BookingSaver")

# Environment -----------------------------------------------------------------
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is missing - set env or .env file")

# RegEx for Booking.com URLs (accepts country TLDs & params) -------------------
BOOKING_RE = re.compile(r"https?://(?:www\.)?booking\.com/\S+", re.IGNORECASE)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle every text message and process any Booking.com URLs."""
    if not update.message or not update.message.text:
        return

    urls: List[str] = BOOKING_RE.findall(update.message.text)
    if not urls:
        return  # nothing to do

    for url in urls:
        try:
            log.info("Scraping %s", url)
            data = scraper.fetch_listing(url)  # blocking, quick enough
            city = data["address"].split(",")[0]
            from google_maps_service import fetch_google_maps_review
            maps= fetch_google_maps_review(data["name"], city)
            data.update(maps)
            # Check if listing already exists
            if db.listing_exists(data):
                await update.message.reply_text(
                    f"⚠️ Duplicate: {data['name']} with these dates ({data['checkin']} - {data['checkout']}) "
                    f"already exists in your saved listings."
                )
            else:
                db.insert_listing(data)
                sheets.append_row(data)
                await update.message.reply_text(f"Saved ✅ {data['name']}")

        except Exception as exc:  # broad catch is fine for a bot
            log.exception("Failed to process %s", url)
            await update.message.reply_text(f"⚠️ Error: {exc}")

def main() -> None:
    """Entry‑point."""
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    log.info("BookingSaver bot started – polling…")
    application.run_polling()


if __name__ == "__main__":
    main()
