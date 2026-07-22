# Market Ingest

A high-performance, stateful market data ingestion pipeline designed for algorithmic trading systems. `market-ingest` fetches historical and real-time equity data, automatically reshapes complex multi-index structures into strict long-form datasets, and persists them into a local DuckDB instance.

It features built-in metadata tracking for **incremental updates**, ensuring your system only downloads new data since the last successful run, minimizing latency and API overhead.

## Features

* **Stateful Incremental Ingestion:** Automatically tracks the `last_update_date` via a local metadata configuration. Subsequent pipeline runs automatically resume from where they left off.
* **Optimized DuckDB Storage:** Natively integrates with DuckDB, automatically initializing tables with `DOUBLE` precision to prevent 32-bit floating-point drift, and uses `ON CONFLICT` logic for seamless upserts.
* **Indian Market Optimization:** Automatically detects and appends the `.NS` suffix to tickers for seamless fetching of National Stock Exchange (NSE) equities.
* **Standardized Schema:** Flattens multi-index DataFrames into a strict, long-form schema ready for quantitative modeling.

## Installation

Install the package in your environment (an editable install is recommended for active development):

```bash
# Clone the repository and install
pip install -e .
```

> Requirements: Python 3.10+, yfinance, duckdb, pandas, pyyaml.

## Usage

The primary entry point is the DataIngestPipeline, which orchestrates the fetching, storing, and metadata updating.

1. Standard Incremental Load (Recommended)  
By not specifying dates, the pipeline checks config/metadata.json. If it's the first run, it defaults to downloading the last 3 months. On future runs, it automatically fetches only the data from the last update date to the current date.

```python
from market_ingest.pipeline import DataIngestPipeline

# Initialize the pipeline for a basket of stocks
pipeline = DataIngestPipeline(
    tickers = ["RELIANCE", "TCS", "HDFCBANK"], # .NS is automatically appended
    interval = "1d"
)

# Execute the fetch, store, and metadata update
pipeline.main()
```

2. Explicit Historical Load  
If you want to bypass the metadata tracker and pull a specific historical window, pass the dates explicitly.

```python
from market_ingest.pipeline import DataIngestPipeline

pipeline = DataIngestPipeline(
    tickers = "INFY",
    start_date = "2024-01-01",
    end_date = "2024-12-31",
    interval = "1wk"
)

pipeline.main()
```