# === Python Modules ===
from typing import List, Optional, Dict, Literal
import duckdb
import pandas as pd

# === Important Functions ta handle duckdb data ===
def call_db_data(
        tickers: List[str] | str,
        interval: Literal["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"] = "1d",
        limit: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        columns: Optional[List[str]] = None,
        desc: bool = True,
        file_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Query historical stock data from DuckDB for specific tickers and parameters.

    Args:
        - tickers (List[str] | str): Ticker symbol or list of symbols.
        - interval (str): Timeframe interval (e.g., '1d', '15m'). Used to resolve file_path if not provided.
        - start_date (Optional[str]): Start date bound ('YYYY-MM-DD'). Defaults to None.
        - end_date (Optional[str]): End date bound ('YYYY-MM-DD'). Defaults to None.
        - columns (Optional[List[str]]): Specific columns to fetch. Defaults to all ('*').
        - desc (bool): Sort order for Date column. Defaults to True (newest first).
        - limit (Optional[int]): Max rows to return. Set to None for all data.
        - file_path (Optional[str]): Explicit path to DuckDB file. Defaults to 'data/{interval}/market_data.db'.

    Returns:
        pd.DataFrame: Query result as a Pandas DataFrame.
    """
    ## === File Path ===
    if file_path is None:
        file_path = f"data/{interval}/market_data.db"

    ## === Normalise Tickers ===
    tickers = [tickers] if isinstance(tickers, str) else tickers
    tickers_list = [t if t.endswith(".NS") else f"{t}.NS" for t in tickers]

    # === Format the Python list into a valid SQL tuple string: ('RELIANCE.NS', 'TCS.NS') ===
    tickers_tuple = tuple(tickers_list) if len(tickers_list) > 1 else f"('{tickers_list[0]}')"

    ## === Select Columns ===
    select_cols = ", ".join(columns) if columns else "*"

    ## === Date Range Clauses ===
    start_clause = f"AND Date >= '{start_date}'" if start_date else ""
    end_clause = f"AND Date <= '{end_date}'" if end_date else ""

    ## === Order ===
    order_clause = "ORDER BY Date DESC" if desc is True else "ORDER BY Date ASC"

    ## === Limit ===
    if limit is not None:
        calc_limit = limit * len(tickers_list)
        limit_clause = f"LIMIT {calc_limit}"
    else:
        limit_clause = ""

    ## === Building Query ===
    query = f"""
        SELECT {select_cols} FROM market_data
        WHERE Ticker IN {tickers_tuple}
        {start_clause}
        {end_clause}
        {order_clause}
        {limit_clause}
    """

    ## === Executing the Query ===
    try:
        with duckdb.connect(file_path) as conn:
            data = conn.execute(query).fetchdf()

        return data

    except Exception as e:
        raise ValueError("Could not call data from duckdb database: {e}.")

def map_by_ticker(
        data: pd.DataFrame,
        ticker_column_name: str = "Ticker"
) -> Dict[str, pd.DataFrame]:
    """
    Splits a long-form market DataFrame into a dictionary of DataFrames keyed by Ticker.

    Args:
        - data (pd.DataFrame): Master DataFrame containing historical data for all the tickers.
        - ticker_column_name (str): Name of the column containing the names of the tickers.

    returns:
        Dict[str, pd.DataFrame]: Mapping of ticker symbol to its respective DataFrame.
    """
    if data.empty:
        raise ValueError("Provided DataFrame is empty. Cannot split empty data.")

    if ticker_column_name not in data.columns:
        raise ValueError(f"Column '{ticker_column_name}' not found in DataFrame. Available columns are: {list(data.columns)}")

    try:
        return {
            ticker: group.drop(columns = [ticker_column_name]).reset_index(drop = True)
            for ticker, group in data.groupby(ticker_column_name)
        }

    except Exception as e:
        raise ValueError(f"Failed to partition DataFrame by column '{ticker_column_name}': {e}")