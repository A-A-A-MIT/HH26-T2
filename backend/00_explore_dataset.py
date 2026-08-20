"""
00_explore_dataset.py - Local Parquet Schema Inspector
Inspects the schema of your locally stored MSMARCO-XI parquet file.

pip install pandas pyarrow duckdb
"""

import os
import sys
import pandas as pd

# Set this to your local parquet file location
LOCAL_PATH = r"MSMARCO-XI/train/hintrain.parquet"

# Fallback path auto-detection if the relative path differs slightly
if not os.path.exists(LOCAL_PATH):
    for alt in ["hintrain.parquet", "MSMARCO-XI/hintrain.parquet"]:
        if os.path.exists(alt):
            LOCAL_PATH = alt
            break

print(f"Loading local parquet file from: {LOCAL_PATH}...", flush=True)

try:
    df = pd.read_parquet(LOCAL_PATH)
except Exception as e:
    print(f"pandas.read_parquet failed ({e}), falling back to DuckDB...", flush=True)
    import duckdb

    df = duckdb.sql(f"SELECT * FROM read_parquet('{LOCAL_PATH}')").df()

print("\n=== Dataset structure ===")
print(f"Shape: {df.shape}")
print(f"Columns: {list(df.columns)}")
print(df.dtypes)

print("\n=== Sample rows ===")
for i in range(min(3, len(df))):
    print(f"\n--- Row {i} ---")
    for col in df.columns:
        val = df.iloc[i][col]
        print(f"{col}: {str(val)[:300]}")

print(f"\nTotal rows: {len(df)}")