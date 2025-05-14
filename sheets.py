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

# New header order with Overall Score before other review metrics
HEADER_TITLES = [
    "Name",
    "Address",
    "Distance",
    "Overall Score",
    "Review Score",
    "Reviews Count",
    "Google Review Score",
    "Google Reviews Count",
    "Google Maps URL",
    "Price",
    "Price per Night",
    "Check-in",
    "Check-out",
    "Nights & Adults",
    "Unit",
    "Free Cancellation",
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

    # First clear all existing conditional formatting
    clear_formatting_request = {
        "deleteConditionalFormatRule": {
            "sheetId": sheet_id,
            "index": 0,
            "allRules": True
        }
    }
    
    try:
        sheets.batchUpdate(spreadsheetId=SHEET_ID, body={"requests": [clear_formatting_request]}).execute()
    except:
        # Ignore errors if no rules exist
        pass

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
        # Conditional formatting: Overall Score (col D idx 3)
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": sheet_id, "startColumnIndex": 3, "endColumnIndex": 4}],
                    "booleanRule": {
                        "condition": {"type": "NUMBER_GREATER_THAN_EQ", "values": [{"userEnteredValue": "9"}]},
                        "format": {"backgroundColor": {"red": 0.5, "green": 0.9, "blue": 0.5}}
                    }
                },
                "index": 0
            }
        },
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": sheet_id, "startColumnIndex": 3, "endColumnIndex": 4}],
                    "booleanRule": {
                        "condition": {
                            "type": "NUMBER_BETWEEN",
                            "values": [{"userEnteredValue": "8"}, {"userEnteredValue": "9"}]
                        },
                        "format": {"backgroundColor": {"red": 0.7, "green": 0.9, "blue": 0.7}}
                    }
                },
                "index": 1
            }
        },
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": sheet_id, "startColumnIndex": 3, "endColumnIndex": 4}],
                    "booleanRule": {
                        "condition": {
                            "type": "NUMBER_BETWEEN",
                            "values": [{"userEnteredValue": "7"}, {"userEnteredValue": "8"}]
                        },
                        "format": {"backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.6}}
                    }
                },
                "index": 2
            }
        },
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": sheet_id, "startColumnIndex": 3, "endColumnIndex": 4}],
                    "booleanRule": {
                        "condition": {
                            "type": "NUMBER_BETWEEN",
                            "values": [{"userEnteredValue": "6"}, {"userEnteredValue": "7"}]
                        },
                        "format": {"backgroundColor": {"red": 1, "green": 0.9, "blue": 0.6}}
                    }
                },
                "index": 3
            }
        },
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": sheet_id, "startColumnIndex": 3, "endColumnIndex": 4}],
                    "booleanRule": {
                        "condition": {"type": "NUMBER_LESS", "values": [{"userEnteredValue": "6"}]},
                        "format": {"backgroundColor": {"red": 1, "green": 0.7, "blue": 0.7}}
                    }
                },
                "index": 4
            }
        },
        # Conditional formatting: Review Score (col E idx 4)
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": sheet_id, "startColumnIndex": 4, "endColumnIndex": 5}],
                    "booleanRule": {
                        "condition": {"type": "NUMBER_GREATER", "values": [{"userEnteredValue": "8"}]},
                        "format": {"backgroundColor": {"red": 0.8, "green": 1, "blue": 0.8}}
                    }
                },
                "index": 5
            }
        },
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": sheet_id, "startColumnIndex": 4, "endColumnIndex": 5}],
                    "booleanRule": {
                        "condition": {
                            "type": "NUMBER_BETWEEN",
                            "values": [{"userEnteredValue": "7"}, {"userEnteredValue": "8"}]
                        },
                        "format": {"backgroundColor": {"red": 1, "green": 1, "blue": 0.6}}
                    }
                },
                "index": 6
            }
        },
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": sheet_id, "startColumnIndex": 4, "endColumnIndex": 5}],
                    "booleanRule": {
                        "condition": {"type": "NUMBER_LESS", "values": [{"userEnteredValue": "7"}]},
                        "format": {"backgroundColor": {"red": 1, "green": 0.8, "blue": 0.8}}
                    }
                },
                "index": 7
            }
        },
        # Conditional formatting: Reviews Count (col F idx 5)
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": sheet_id, "startColumnIndex": 5, "endColumnIndex": 6}],
                    "booleanRule": {
                        "condition": {"type": "NUMBER_GREATER", "values": [{"userEnteredValue": "75"}]},
                        "format": {"backgroundColor": {"red": 0.8, "green": 1, "blue": 0.8}}
                    }
                },
                "index": 8
            }
        },
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": sheet_id, "startColumnIndex": 5, "endColumnIndex": 6}],
                    "booleanRule": {
                        "condition": {
                            "type": "NUMBER_BETWEEN",
                            "values": [{"userEnteredValue": "10"}, {"userEnteredValue": "75"}]
                        },
                        "format": {"backgroundColor": {"red": 1, "green": 1, "blue": 0.6}}
                    }
                },
                "index": 9
            }
        },
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": sheet_id, "startColumnIndex": 5, "endColumnIndex": 6}],
                    "booleanRule": {
                        "condition": {"type": "NUMBER_LESS", "values": [{"userEnteredValue": "10"}]},
                        "format": {"backgroundColor": {"red": 1, "green": 0.8, "blue": 0.8}}
                    }
                },
                "index": 10
            }
        },
        # Conditional formatting: Google Review Score (col G idx 6)
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": sheet_id, "startColumnIndex": 6, "endColumnIndex": 7}],
                    "booleanRule": {
                        "condition": {"type": "NUMBER_GREATER_THAN_EQ", "values": [{"userEnteredValue": "4.4"}]},
                        "format": {"backgroundColor": {"red": 0.8, "green": 1, "blue": 0.8}}
                    }
                },
                "index": 11
            }
        },
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": sheet_id, "startColumnIndex": 6, "endColumnIndex": 7}],
                    "booleanRule": {
                        "condition": {
                            "type": "NUMBER_BETWEEN",
                            "values": [{"userEnteredValue": "4"}, {"userEnteredValue": "4.4"}]
                        },
                        "format": {"backgroundColor": {"red": 1, "green": 1, "blue": 0.6}}
                    }
                },
                "index": 12
            }
        },
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": sheet_id, "startColumnIndex": 6, "endColumnIndex": 7}],
                    "booleanRule": {
                        "condition": {"type": "NUMBER_LESS", "values": [{"userEnteredValue": "4"}]},
                        "format": {"backgroundColor": {"red": 1, "green": 0.8, "blue": 0.8}}
                    }
                },
                "index": 13
            }
        },
        # Conditional formatting: Google Reviews Count (col H idx 7)
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": sheet_id, "startColumnIndex": 7, "endColumnIndex": 8}],
                    "booleanRule": {
                        "condition": {"type": "NUMBER_GREATER", "values": [{"userEnteredValue": "250"}]},
                        "format": {"backgroundColor": {"red": 0.8, "green": 1, "blue": 0.8}}
                    }
                },
                "index": 14
            }
        },
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": sheet_id, "startColumnIndex": 7, "endColumnIndex": 8}],
                    "booleanRule": {
                        "condition": {
                            "type": "NUMBER_BETWEEN",
                            "values": [{"userEnteredValue": "50"}, {"userEnteredValue": "250"}]
                        },
                        "format": {"backgroundColor": {"red": 1, "green": 1, "blue": 0.6}}
                    }
                },
                "index": 15
            }
        },
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": sheet_id, "startColumnIndex": 7, "endColumnIndex": 8}],
                    "booleanRule": {
                        "condition": {"type": "NUMBER_LESS", "values": [{"userEnteredValue": "50"}]},
                        "format": {"backgroundColor": {"red": 1, "green": 0.8, "blue": 0.8}}
                    }
                },
                "index": 16
            }
        },
        # Conditional formatting: Free Cancellation (col P idx 15)
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": sheet_id, "startColumnIndex": 15, "endColumnIndex": 16}],
                    "booleanRule": {
                        "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "Yes"}]},
                        "format": {"backgroundColor": {"red": 0.8, "green": 1, "blue": 0.8}}
                    }
                },
                "index": 17
            }
        }
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

    # Calculate Overall Score (1-10 scale)
    booking_score = float(rec.get("review_score", 0)) if rec.get("review_score") else 0
    booking_count = int(rec.get("reviews_count", 0)) if rec.get("reviews_count") else 0
    google_score = float(rec.get("google_review_score", 0)) if rec.get("google_review_score") else 0
    google_count = int(rec.get("google_reviews_count", 0)) if rec.get("google_reviews_count") else 0
    
    # Use Booking.com score directly (already 0-10 scale)
    booking_score_adj = booking_score if booking_score else 0
    
    # Convert Google's 5-point scale to 10-point scale
    google_score_adj = google_score * 2 if google_score else 0
    
    # Weight factors based on review counts
    booking_weight = min(booking_count / 100, 1) if booking_count else 0
    google_weight = min(google_count / 200, 1) if google_count else 0
    
    # Calculate weighted average, with penalty for missing Google reviews
    if booking_score and google_score:
        overall_score = ((booking_score_adj * booking_weight) + (google_score_adj * google_weight)) / (booking_weight + google_weight)
    elif booking_score:
        # Apply a 10% penalty for missing Google reviews
        overall_score = booking_score_adj * 0.9
    elif google_score:
        overall_score = google_score_adj
    else:
        overall_score = 0
    
    # Add bonus for free cancellation (0.5 points)
    cancellation = rec.get("cancellation", "").lower()
    if cancellation == "yes" or "free" in cancellation:
        overall_score += 0.5
        
    # Ensure score is between 1-10 and round to 1 decimal
    overall_score = round(max(min(overall_score, 10), 1) if overall_score else 0, 1)

    # Build row: hyperlink Name and Google Maps URL
    link = rec.get("link", "")
    name = rec.get("name", "")
    name_hyper = f'=HYPERLINK("{link}", "{name}")'

    # Handle missing or search-only Google Maps URL
    google_maps_url = rec.get("google_maps_url", None)
    
    # If google_maps_url is None, there's no valid match on Google Maps
    if google_maps_url is None:
        maps_hyper = "No Match"
    else:
        maps_hyper = f'=HYPERLINK("{google_maps_url}", "Link")'

    row = [
        name_hyper,
        rec.get("address"),
        rec.get("distance"),
        overall_score if overall_score else "",
        rec.get("review_score"),
        rec.get("reviews_count"),
        rec.get("google_review_score"),
        rec.get("google_reviews_count"),
        maps_hyper,
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
