"""
SQLite persistence for BookingSaver.
"""

import sqlite3
from pathlib import Path
from typing import Dict

DB_PATH = Path("data/bookings.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS listings (
    hotel_id       INTEGER,
    name           TEXT,
    link           TEXT,
    address        TEXT,
    distance       TEXT,
    checkin        TEXT,
    checkout       TEXT,
    review_score   REAL,
    reviews_count  INTEGER,
    google_review_score REAL,
    google_reviews_count  INTEGER,
    google_maps_url TEXT,
    overall_score  REAL,
    unit           TEXT,
    cancellation   TEXT,
    nights_adults  TEXT,
    price          TEXT,
    price_per_night REAL,
    scraped_at     TEXT,
    source_url     TEXT,
    PRIMARY KEY (hotel_id, link, checkin, checkout)
);
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(SCHEMA)
        conn.commit()


def insert_listing(rec: Dict) -> None:
    keys = ", ".join(rec.keys())
    placeholders = ", ".join("?" for _ in rec)
    sql = f"INSERT OR IGNORE INTO listings ({keys}) VALUES ({placeholders})"
    with _connect() as conn:
        conn.execute(sql, tuple(rec.values()))
        conn.commit()

def listing_exists(rec: Dict) -> bool:
    """Check if listing already exists in database with same dates."""
    sql = """
    SELECT 1 FROM listings 
    WHERE link = ? AND checkin = ? AND checkout = ?
    LIMIT 1
    """
    with _connect() as conn:
        result = conn.execute(sql, (rec['link'], rec['checkin'], rec['checkout'])).fetchone()
        return result is not None


if __name__ == "__main__":
    init_db()
    print("SQLite ready ➜ bookings.db")
