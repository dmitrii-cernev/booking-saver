"""
Google Sheets helper for BookingSaver with a single main sheet,
hyperlink formatting, conditional formatting, and price-per-night.
Requires a *service-account* JSON either as env-var string
(GOOGLE_CREDENTIALS_JSON) or a path to the file.
"""
import json
import os
import re
from typing import Dict, List

from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

load_dotenv()
SHEET_ID = os.getenv("SHEET_ID")
if not SHEET_ID:
    raise RuntimeError("SHEET_ID env var is missing")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# New header order with checkin/checkout
HEADER_TITLES = [
    "Name",
    "Address",
    "Distance",
    "Review Score",
    "Reviews Count",
    "Price",
    "Price per Night",
    "Check-in",
    "Check-out",
    "Nights & Adults",
    "Unit",
    "Cancellation",
]


def _credentials() -> Credentials:
    creds_env = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if not creds_env:
        raise RuntimeError("GOOGLE_CREDENTIALS_JSON env var is missing")
    if os.path.isfile(creds_env):
        return Credentials.from_service_account_file(creds_env, scopes=SCOPES)
    return Credentials.from_service_account_info(json.loads(creds_env), scopes=SCOPES)


def init_sheet() -> None:
    """
    Initialize the main sheet: write headers and apply formatting.
    """
    creds = _credentials()
    service = build("sheets", "v4", credentials=creds, cache_discovery=False)
    sheets = service.spreadsheets()

    # Write header row
    sheets.values().update(
        spreadsheetId=SHEET_ID,
        range="A1",
        valueInputOption="RAW",
        body={"values": [HEADER_TITLES]},
    ).execute()

    # Get sheetId of the first tab
    meta = sheets.get(spreadsheetId=SHEET_ID).execute()
    sheet_id = meta["sheets"][0]["properties"]["sheetId"]

    # Build formatting requests (bold header, freeze, conditional rules)
    requests = [
        # Bold + grey header
        {
            "repeatCell": {
                "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1},
                "cell": {
                    "userEnteredFormat": {
                        "textFormat": {"bold": True},
                        "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9},
                    }
                },
                "fields": "userEnteredFormat(textFormat,backgroundColor)",
            }
        },
        # Freeze top row
        {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": sheet_id,
                    "gridProperties": {"frozenRowCount": 1},
                },
                "fields": "gridProperties.frozenRowCount",
            }
        },
        # (plus your existing conditional formatting rules for review score & count)…
    ]
    sheets.batchUpdate(spreadsheetId=SHEET_ID, body={"requests": requests}).execute()


def append_row(rec: Dict) -> None:
    """Append a dict as a new row in the single main sheet."""
    creds = _credentials()
    service = build("sheets", "v4", credentials=creds, cache_discovery=False)
    sheets = service.spreadsheets()

    # Compute price per night
    nights_text = rec.get("nights_adults", "0 nights")
    m = re.search(r"(\d+)\s+nights", nights_text)
    nights = int(m.group(1)) if m else 1
    try:
        price_val = float(rec.get("price", "0").replace(",", ""))
        price_per_night = round(price_val / nights, 2)
    except:
        price_per_night = ""

    # Build row: hyperlink Name
    link = rec.get("link", "")
    name = rec.get("name", "")
    name_hyper = f'=HYPERLINK("{link}", "{name}")'

    row = [
        name_hyper,
        rec.get("address"),
        rec.get("distance"),
        rec.get("review_score"),
        rec.get("reviews_count"),
        rec.get("price"),
        price_per_night,
        rec.get("checkin"),
        rec.get("checkout"),
        rec.get("nights_adults"),
        rec.get("unit"),
        rec.get("cancellation"),
    ]

    sheets.values().append(
        spreadsheetId=SHEET_ID,
        range="A2",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": [row]},
    ).execute()
