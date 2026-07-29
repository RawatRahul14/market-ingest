# === Python Modules ===
import os
import json
import time
from typing import Dict, Literal
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler

# === Metadata Update ===
def update_metadata(
        today_date: str | None = None,
        file_path: str = "config/metadata.json"
) -> None:
    """
    Updates the metadata JSON file with the provided date.

    Args:
        today_date (str | None): The date to include in the metadata. If None, the current date will be used.
    """
    try:

        ## === Metadata to be saved ===
        metadata = {
            "last_update_date": today_date if today_date else time.strftime("%Y-%m-%d"),
        }

        ## === Ensure Directory Exists ===
        os.makedirs(
            os.path.dirname(file_path),
            exist_ok = True
        )

        ## === Save Metadata to JSON File ===
        with open(file_path, "w") as f:
            json.dump(
                metadata,
                f,
                indent = 4
            )

    except Exception as e:
        print(f"Error creating metadata: {e}")
        return None

# === Call Metadata File ===
def call_metadata(
        file_path: str = "config/metadata.json"
) -> Dict[str, str] | None:
    """
    Reads the metadata JSON file and returns its contents as a dictionary.

    Args:
        file_path (str): The path to the metadata JSON file.
    """
    try:
        ## === Check if Metadata File Exists ===
        if not os.path.exists(file_path):
            return {
                "last_update_date": None
            }

        ## === Read Metadata from JSON File ===
        with open(file_path, "r") as f:
            metadata = json.load(f)
        return metadata

    except FileNotFoundError:
        raise ValueError(f"Metadata file not found at {file_path}.")

# === Logger Directory ===
LOG_DIR = Path("logs")
LOG_DIR.mkdir(
    exist_ok = True
)

# === Logger Function ===
def get_logger(
        name: Literal[
            "FETCHER",
            "PIPELINE",
            "UTILS",
            "MAIN"
        ],
        log_file: str = "market_ingest.log",
        level: int = logging.INFO
) -> logging.Logger:
    """
    Returns a configured logger for the market-ingest package.
    """
    logger = logging.getLogger(name=name)

    ## === Returns if the logger already exists ===
    if logger.handlers:
        return logger
    
    ## === Configuring the logger ===
    logger.setLevel(level = level)

    formatter = logging.Formatter(
        fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt = "%Y-%m-%d %H:%M:%S"
    )

    ## === File Handler ===
    # 10 MB per file, keep 5 backups
    file_handler = RotatingFileHandler(
        filename = LOG_DIR / log_file,
        maxBytes = 10_485_760, 
        backupCount = 5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    ## === Console Handler ===
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)  # Changed to INFO so users see progress

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.propagate = False

    return logger