# === Python Modules ===
from typing import TypedDict

# === Schema Definitions ===
class StockDataSchema(TypedDict):
    """
    Defines the schema for the stock data fetched from Yahoo Finance.
    """
    Date: str
    Ticker: str
    Close: float
    High: float
    Low: float
    Open: float
    Volume: int