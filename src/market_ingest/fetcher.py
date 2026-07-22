# === Python Modules ===
from typing import List, Optional, Literal
import os
import duckdb
import yfinance as yf
import pandas as pd
from yfinance import data

# === Schema Module ===
from .schema import StockDataSchema

# === Valid Interval ===
VALID_INTERVALS: List[str] = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"]

# === Valid Period ===
VALID_PERIODS: List[str] = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]

# ==============================================================================
# Fetcher Class
# ==============================================================================
# Encompasses all methods required for downloading historical stock data from 
# the Yahoo Finance API, reshaping the resulting MultiIndex DataFrames into a 
# standardized long-form format, and cleaning metadata for downstream storage.
# ==============================================================================
class Fetcher:
    def __init__(
            self,
            tickers: List[str] | str,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            interval: Literal["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"] = "1d",
            period: Literal["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"] = None,
            db_path: Optional[str] = None
    ):
        """
        Initialize the Fetcher class with the specified parameters.
        """

        ## === Validate the input parameters ===
        if (start_date or end_date) and period:
            raise ValueError("Cannot specify both start/end dates and period. Please choose one.")

        if interval not in VALID_INTERVALS:
            raise ValueError(f"Invalid interval '{interval}'. Valid intervals are: {VALID_INTERVALS}")

        if (period not in VALID_PERIODS) and period is not None:
            raise ValueError(f"Invalid period '{period}'. Valid periods are: {VALID_PERIODS}")

        ## === Store the parameters as instance variables ===
        self.tickers = [tickers] if isinstance(tickers, str) else tickers

        ## === Adding '.NS' at the end of each ticker if not present ===
        self.tickers = [ticker if ticker.endswith(".NS") else f"{ticker}.NS" for ticker in self.tickers]

        if start_date is not None:
            self.period = None
            self.start_date = start_date

            if end_date is not None:
                self.end_date = end_date
            else:
                self.end_date = pd.Timestamp.now().strftime("%Y-%m-%d")

        else:
            self.start_date = None
            self.end_date = None

            if period is None:
                self.period = "1mo"
            else:
                self.period = period

        self.interval = interval

        ## === Database Path and Initialization ===
        if db_path is None:
            self.db_path = f"data/{interval}/market_data.db"
        else:
            self.db_path = db_path

        self._init_db()

        ## === Determine the number of threads to use for parallel processing ===
        self.n_threads = min(4, os.cpu_count() / 2)

    def _init_db(self) -> None:
        """
        Initialize the database connection and create necessary tables if they don't exist.
        """
        ## === Creates folder and initializes database ===
        try:
            if os.path.exists(self.db_path):

                ## === Database already exists, no need to create ===
                print(f"Database already exists at {self.db_path}.")
            else:

                ## === Create the directory if it doesn't exist ===
                dir_name = os.path.dirname(self.db_path)

                if dir_name:
                    os.makedirs(
                        dir_name,
                        exist_ok = True
                    )
                print(f"Database initialized at {self.db_path}.")

        except Exception as e:
            print(f"Error initializing database: {e}")

        try:
            ## === Create the database connection ===
            with duckdb.connect(self.db_path) as conn:

                ## === Create the table if it doesn't exis  t ===
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS market_data (
                        Date TIMESTAMP,
                        Ticker VARCHAR,
                        Close DOUBLE,
                        High DOUBLE,
                        Low DOUBLE,
                        Open DOUBLE,
                        Volume BIGINT,
                        PRIMARY KEY (Date, Ticker)
                    )
                    """
                    )
                
                ## === Create an index on the Date and Ticker columns for faster queries ===
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_date_ticker ON market_data (Date, Ticker)
                    """
                )

        except Exception as e:  
            print(f"Error creating table: {e}")

    def fetch_data(
            self
    ) -> StockDataSchema:
        """
        Fetch historical stock data for the specified tickers and parameters.
        Returns:
            StockDataSchema: A DataFrame containing the fetched stock data.
        """
        try:
            ## === Fetch the stock data ===

            ### === Use the appropriate method based on whether start/end dates or period is specified ===
            if self.start_date and self.end_date:
                data = yf.download(
                    tickers = self.tickers,
                    start = self.start_date,
                    end = self.end_date,
                    interval = self.interval,
                    auto_adjust = True,
                    threads = self.n_threads
                )
            else:
                data = yf.download(
                    tickers = self.tickers,
                    period = self.period,
                    interval = self.interval,
                    auto_adjust = True,
                    threads = self.n_threads
                )

            ## === If no data is fetched ===
            if data.empty:
                print("No data fetched. Please check the tickers and parameters.")
                return pd.DataFrame(
                    columns = ["Date", "Ticker", "Close", "High", "Low", "Open", "Volume"]
                )

            ## === Reshape the DataFrame into a long-form format ===
            data_stacked = data.stack(level = "Ticker").reset_index()

            ## === Sort the DataFrame by Ticker and Date ===
            data_stacked = data_stacked.sort_values(
                by = ["Ticker", "Date"]
            ).reset_index(drop = True)

            ## === Nuke the lingering axis names (like "Price") ===
            data_stacked.rename_axis(
                None,
                axis = 1,
                inplace = True
            )
            data_stacked.index.name = None

            ## === Round the numeric columns to a reasonable number of decimal places ===
            numeric_columns = ["Close", "High", "Low", "Open"]
            data_stacked[numeric_columns] = data_stacked[numeric_columns].round(2)

            return data_stacked

        except Exception as e: 
            print(f"Error fetching data: {e}")
            return pd.DataFrame(
                columns = ["Date", "Ticker", "Close", "High", "Low", "Open", "Volume"]
            )

    def store_data(
            self,
            data: StockDataSchema
    ) -> None:
        """
        Store the fetched stock data into the database.
        Args:
            data (StockDataSchema): A DataFrame containing the stock data to be stored.
        """
        ## === Store the data into the database ===
        try:
            with duckdb.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO market_data (Date, Ticker, Close, High, Low, Open, Volume)
                    SELECT
                        Date, Ticker, Close, High, Low, Open, Volume
                    FROM data
                    ON CONFLICT (Date, Ticker) DO UPDATE SET
                        Close = EXCLUDED.Close,
                        High = EXCLUDED.High,
                        Low = EXCLUDED.Low,
                        Open = EXCLUDED.Open,
                        Volume = EXCLUDED.Volume
                    """
                )

        except Exception as e:
            print(f"Error storing data: {e}")