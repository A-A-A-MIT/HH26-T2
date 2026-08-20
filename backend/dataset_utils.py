"""
Shared loader for ai4bharat/MSMARCO-XI.

`datasets.load_dataset()` hits a known pyarrow bug on this file — its
`passages` column is a struct-of-lists (English_passages, Translated_passages,
is_selected), and the datasets library's arrow-batching code chokes on it.

Fix: skip `datasets` entirely. Pull the raw parquet with huggingface_hub and
read it with plain pandas (falling back to duckdb if pandas/pyarrow still
trips on it). Every other script imports `load_train_df()` from here so the
fix only has to live in one place.

pip install huggingface_hub pandas pyarrow duckdb
"""
from huggingface_hub import hf_hub_download

REPO_ID = "ai4bharat/MSMARCO-XI"
TRAIN_FILE = "train/hintrain.parquet"


def _download_path():
    return hf_hub_download(repo_id=REPO_ID, repo_type="dataset", filename=TRAIN_FILE)


def load_train_df():
    """
    Returns the full 'train' split as a pandas DataFrame.

    Tries pandas.read_parquet first (fast path, works most of the time).
    Falls back to duckdb's parquet reader if pandas/pyarrow can't handle the
    nested `passages` struct column — duckdb uses its own engine and is much
    more reliable on messy nested parquet.
    """
    path = _download_path()

    try:
        import pandas as pd
        return pd.read_parquet(path)
    except Exception as e:
        print(f"pandas.read_parquet failed ({e}); falling back to duckdb...")
        import duckdb
        return duckdb.sql(f"SELECT * FROM read_parquet('{path}')").df()
