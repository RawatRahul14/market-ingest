# === Python Modules ===
import pytest

# === Custom Modules ===
from market_ingest import Fetcher

# === Test Cases ===
def test_fetcher_validation_conflict():
    """
    Asserts that choosing both a date window and a tracking period raises ValueError.
    """
    ## === Conflicting date window and period ===
    with pytest.raises(
        ValueError, 
        match = "Cannot specify both start/end dates and period"
    ):
        Fetcher(
            tickers = "AAPL",
            start_date = "2026-01-01",
            period = "1y"
        )

def test_fetcher_validation_invalid_interval():
    """
    Asserts that unsupported interval frequencies reject initialization.
    """
    ## === Invalid interval frequency ===
    with pytest.raises(
        ValueError,
        match = "Invalid interval"
    ):
        Fetcher(
            tickers = "AAPL",
            interval = "99d"
        )

def test_fetcher_string_ticker_conversion():
    """
    Validates that a single raw string ticker parameter down-casts into a uniform list.
    """
    ## === Single string ticker ===
    f = Fetcher(
        tickers = "AAPL"
    )
    assert f.tickers == ["AAPL"]
    
    f_list = Fetcher(
        tickers = ["AAPL", "MSFT"]
    )
    assert f_list.tickers == ["AAPL", "MSFT"]