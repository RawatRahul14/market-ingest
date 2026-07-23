# === Python Modules ===
import time
from typing import List, Literal, Optional

# === Component Imports ===
from market_ingest.fetcher import Fetcher

# === Utils ===
from market_ingest.utils import update_metadata, call_metadata

# === Data Ingest Pipeline ===
class DataIngestPipeline:
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
        Initializes the DataIngestPipeline class with the specified parameters.

        Args:
            tickers (List[str] | str): A list of stock tickers or a single ticker as a string.
            start_date (Optional[str]): The start date for data fetching in 'YYYY-MM-DD' format. Defaults to None.
            end_date (Optional[str]): The end date for data fetching in 'YYYY-MM-DD' format. Defaults to None.
            interval (Literal): The data interval. Defaults to "1d".
            period (Literal): The data period. Defaults to None.
            db_path (Optional[str]): The path to the database file. Defaults to None.
        """
        ## === Store Base Parameters ===
        self.tickers = tickers
        self.interval = interval
        self.db_path = db_path
        
        ## === Initialize Date/Period Variables ===
        self.start_date = None
        self.end_date = None
        self.period = None

        ## === If Start Date is not Provided ===
        if start_date is None:
            metadata_dict = call_metadata()

            ### === If Metadata File Does Not Exist or Last Update Date is None ===
            if metadata_dict.get("last_update_date") is None:

                ### === If Period is Not Provided, Use Default 3mo ===
                if period is None:
                    self.period = "3mo"
                else:
                    self.period = period

            ### === If Metadata File Exists ===
            else:
                self.start_date = metadata_dict.get("last_update_date")

                ### === If End Date is Not Provided, Use Current Date ===
                if end_date is not None:
                    self.end_date = end_date

        ## === If Start Date is Provided ===
        else:
            self.start_date = start_date

            ### === If End Date is Not Provided, Use Current Date ===
            if end_date is not None:
                self.end_date = end_date

    def main(
            self
    ) -> None:
        """
        Main method to execute the data ingestion pipeline.

        This method initializes the Fetcher class with the specified parameters and calls its main method
        to fetch and store data. After successful data ingestion, it updates the metadata with the last update date.

        Returns:
            None
        """
        try:

            ### === Validate Date Range ===
            if self.start_date == self.end_date:
                print(f"Start date and end date are both {self.start_date}. Could not download new data. Ending pipeline.")
                return
            
            ## === Initialize Fetcher Class ===
            fetcher = Fetcher(
                tickers = self.tickers,
                start_date = self.start_date,
                end_date = self.end_date,
                interval = self.interval,
                period = self.period,
                db_path = self.db_path
            )

            ## === Fetching and Storing data ===
            fetcher.store_data(
                data = fetcher.fetch_data()
            )

            ## === Update Metadata After Successful Data Ingestion ===
            update_metadata(today_date = self.end_date if self.end_date is not None else None)

        except Exception as e:
            raise ValueError(f"An error occurred during the data ingestion process: {e}")