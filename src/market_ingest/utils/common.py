# === Python Modules ===
import os
import json
import time
from typing import Dict

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