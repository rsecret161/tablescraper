import pandas as pd


def fetch_tables(url):
    try:
        tables = pd.read_html(url)
        return tables
    except Exception as exc:
        raise RuntimeError(f"Error fetching tables: {exc}")
