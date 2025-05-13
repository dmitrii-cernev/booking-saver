"""
Google Sheets helper for BookingSaver with a single main sheet,
hyperlink formatting, conditional formatting on review and reviews count,
and price-per-night functionality.
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

# Header titles for the single sheet
HEADER_TITLES = [
    "Name",
    "Address",
    "Distance",
    "Review Score",
    "Reviews Count",
    "Nights & Adults",
    "Price",
    "Price per Night",
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
    sheets_service = service.spreadsheets()

    # Write header row on the default sheet (first tab)
    sheets_service.values().update(
        spreadsheetId=SHEET_ID,
        range="A1",
        valueInputOption="RAW",
        body={"values": [HEADER_TITLES]},
    ).execute()

    # Get sheetId of the first sheet
    meta = sheets_service.get(spreadsheetId=SHEET_ID).execute()
    sheet_id = meta["sheets"][0]["properties"]["sheetId"]

    # Build formatting requests
    requests = []
    # Bold and gray header + freeze first row
    requests.extend([
        {"repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1},
            "cell": {"userEnteredFormat": {"textFormat": {"bold": True},
                                             "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}}},
            "fields": "userEnteredFormat(textFormat,backgroundColor)"
        }},
        {"updateSheetProperties": {
            "properties": {"sheetId": sheet_id, "gridProperties": {"frozenRowCount": 1}},
            "fields": "gridProperties.frozenRowCount"
        }}
    ])
    # Conditional formatting: Review Score (col D idx 3)
    requests.extend([
        {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": sheet_id, "startRowIndex": 1, "startColumnIndex": 3, "endColumnIndex": 4}],
            "booleanRule": {"condition": {"type": "NUMBER_LESS", "values": [{"userEnteredValue": "7"}]},
                               "format": {"backgroundColor": {"red": 1, "green": 0.8, "blue": 0.8}}}}, "index": 0}},
        {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": sheet_id, "startRowIndex": 1, "startColumnIndex": 3, "endColumnIndex": 4}],
            "booleanRule": {"condition": {"type": "NUMBER_BETWEEN", "values": [{"userEnteredValue": "7"}, {"userEnteredValue": "8"}]},
                               "format": {"backgroundColor": {"red": 1, "green": 1, "blue": 0.6}}}}, "index": 1}},
        {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": sheet_id, "startRowIndex": 1, "startColumnIndex": 3, "endColumnIndex": 4}],
            "booleanRule": {"condition": {"type": "NUMBER_GREATER", "values": [{"userEnteredValue": "8"}]},
                               "format": {"backgroundColor": {"red": 0.8, "green": 1, "blue": 0.8}}}}, "index": 2}}
    ])
    # Conditional formatting: Reviews Count (col E idx 4)
    requests.extend([
        {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": sheet_id, "startRowIndex": 1, "startColumnIndex": 4, "endColumnIndex": 5}],
            "booleanRule": {"condition": {"type": "NUMBER_LESS", "values": [{"userEnteredValue": "10"}]},
                               "format": {"backgroundColor": {"red": 1, "green": 0.8, "blue": 0.8}}}}, "index": 3}},
        {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": sheet_id, "startRowIndex": 1, "startColumnIndex": 4, "endColumnIndex": 5}],
            "booleanRule": {"condition": {"type": "NUMBER_BETWEEN", "values": [{"userEnteredValue": "10"}, {"userEnteredValue": "75"}]},
                               "format": {"backgroundColor": {"red": 1, "green": 1, "blue": 0.6}}}}, "index": 4}},
        {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": sheet_id, "startRowIndex": 1, "startColumnIndex": 4, "endColumnIndex": 5}],
            "booleanRule": {"condition": {"type": "NUMBER_GREATER", "values": [{"userEnteredValue": "75"}]},
                               "format": {"backgroundColor": {"red": 0.8, "green": 1, "blue": 0.8}}}}, "index": 5}}
    ])
    # Apply batch formatting
    sheets_service.batchUpdate(spreadsheetId=SHEET_ID, body={"requests": requests}).execute()


def append_row(rec: Dict) -> None:
    """Append a dict as a new row in the single main sheet."""
    creds = _credentials()
    service = build("sheets", "v4", credentials=creds, cache_discovery=False)
    sheets_service = service.spreadsheets()

    # Compute price per night
    nights_text = rec.get("nights_adults", "0 nights")
    m = re.search(r"(\d+)\s+nights", nights_text)
    nights = int(m.group(1)) if m else 1
    try:
        price_val = float(rec.get("price", "0").replace(",", ""))
        price_per_night = round(price_val / nights, 2)
    except:
        price_per_night = None

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
        rec.get("nights_adults"),
        rec.get("price"),
        price_per_night,
        rec.get("unit"),
        rec.get("cancellation"),
    ]

    sheets_service.values().append(
        spreadsheetId=SHEET_ID,
        range="A2",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": [row]},
    ).execute()
