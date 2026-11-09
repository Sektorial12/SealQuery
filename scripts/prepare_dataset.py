#!/usr/bin/env python3
"""Build the deterministic SealQuery demo dataset.

Source: UCI Machine Learning Repository, Online Retail dataset.
The dataset is public. SealQuery uses it as a private-data stand-in and
documents that the privacy claim is about the architecture, not the source.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import sys

import pandas as pd
import requests

SOURCE_URL = (
    "https://archive.ics.uci.edu/ml/machine-learning-databases/00352/"
    "Online%20Retail.xlsx"
)
SAMPLE_ROWS = 5_000
RANDOM_STATE = 42
VERSION = "retail_v1"

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
XLSX_PATH = DATA_DIR / "Online Retail.xlsx"
CSV_PATH = DATA_DIR / f"{VERSION}.csv"
META_PATH = DATA_DIR / f"{VERSION}.meta.json"

CANARY = {
    "InvoiceNo": "CANARY-0001",
    "StockCode": "CANARY",
    "Description": "SEALQUERY CANARY DO NOT EXPOSE",
    "Quantity": 999_999,
    "InvoiceDate": "2011-12-09 12:00:00",
    "UnitPrice": 12_345.67,
    "CustomerID": 99_999,
    "Country": "Canaryland",
}

REQUIRED_COLUMNS = [
    "InvoiceNo",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
    "Country",
]


def download_source() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if XLSX_PATH.exists():
        return

    print(f"Downloading {SOURCE_URL}", file=sys.stderr)
    response = requests.get(SOURCE_URL, timeout=120)
    response.raise_for_status()
    XLSX_PATH.write_bytes(response.content)


def build_dataset() -> dict:
    download_source()

    frame = pd.read_excel(XLSX_PATH)
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise RuntimeError(f"source dataset is missing columns: {missing}")

    frame = frame.dropna(
        subset=["InvoiceNo", "StockCode", "Description", "InvoiceDate", "CustomerID"]
    )
    frame = frame[(frame["Quantity"] > 0) & (frame["UnitPrice"] > 0)]
    frame = frame.sort_values(
        ["InvoiceNo", "StockCode", "InvoiceDate", "CustomerID"],
        kind="mergesort",
    ).reset_index(drop=True)

    if len(frame) < SAMPLE_ROWS:
        raise RuntimeError(f"only {len(frame)} eligible rows, need {SAMPLE_ROWS}")

    sample = frame.sample(n=SAMPLE_ROWS, random_state=RANDOM_STATE)
    sample = sample.sort_values(
        ["InvoiceNo", "StockCode", "InvoiceDate", "CustomerID"],
        kind="mergesort",
    ).reset_index(drop=True)

    sample = pd.concat([sample, pd.DataFrame([CANARY])], ignore_index=True)
    sample["InvoiceDate"] = pd.to_datetime(sample["InvoiceDate"]).dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    sample = sample.sort_values(
        ["InvoiceNo", "StockCode", "InvoiceDate", "CustomerID"],
        kind="mergesort",
    ).reset_index(drop=True)

    sample.to_csv(CSV_PATH, index=False, lineterminator="\n")
    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()

    metadata = {
        "version": VERSION,
        "source": SOURCE_URL,
        "source_license": "UCI Machine Learning Repository Online Retail dataset",
        "sample_rows": SAMPLE_ROWS,
        "canary_rows": 1,
        "total_rows": len(sample),
        "sha256": digest,
        "canary": {
            "invoice_no": CANARY["InvoiceNo"],
            "stock_code": CANARY["StockCode"],
            "country": CANARY["Country"],
            "customer_id": CANARY["CustomerID"],
        },
        "note": (
            "Public dataset used as a private-data stand-in. "
            "The privacy claim is about the SealQuery architecture, not the "
            "secrecy of this public source."
        ),
    }
    META_PATH.write_text(json.dumps(metadata, indent=2) + "\n")
    return metadata


def main() -> None:
    metadata = build_dataset()
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
