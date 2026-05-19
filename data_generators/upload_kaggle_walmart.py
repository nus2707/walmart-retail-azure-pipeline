import pandas as pd
import io
import os
from datetime import datetime
#from azure.storage.file-datalake import DataLakeServiceClient
from azure.storage.filedatalake import DataLakeServiceClient
from azure.identity import DefaultAzureCredential

STORAGE_ACCOUNT = "walmartdata"
CSV_PATH        = "Walmart_Sales.csv"   # path to your downloaded file

def get_adls_client():
    credential = DefaultAzureCredential()
    return DataLakeServiceClient(
        account_url=f"https://{STORAGE_ACCOUNT}.dfs.core.windows.net",
        credential=credential
    )

def upload_parquet(client, df: pd.DataFrame, bronze_path: str):
    fs     = client.get_file_system_client("bronze")
    f      = fs.get_file_client(bronze_path)
    buf    = io.BytesIO()
    df.to_parquet(buf, index=False, engine="pyarrow")
    buf.seek(0)
    f.upload_data(buf.read(), overwrite=True)
    print(f"  Uploaded → bronze/{bronze_path}  ({len(df):,} rows)")

def run():
    print("Reading Walmart_Sales.csv ...")
    df = pd.read_csv(CSV_PATH)

    # ── Basic cleaning before landing in Bronze ──────────────────────
    df.columns  = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df["date"]  = pd.to_datetime(df["date"], dayfirst=True)
    df["ingest_date"]   = datetime.today().strftime("%Y-%m-%d")
    df["source_system"] = "kaggle_walmart_sales"

    print(f"  Shape     : {df.shape}")
    print(f"  Columns   : {list(df.columns)}")
    print(f"  Date range: {df['date'].min()} → {df['date'].max()}")
    print(f"  Stores    : {df['store'].nunique()}")
    print()

    # ── Split by year and upload partitioned ─────────────────────────
    client = get_adls_client()
    for year, year_df in df.groupby(df["date"].dt.year):
        path = f"batch/historical_sales/source=kaggle/year={year}/walmart_sales.parquet"
        upload_parquet(client, year_df.reset_index(drop=True), path)

    # ── Also upload a full unpartitioned copy ─────────────────────────
    upload_parquet(
        client, df,
        "batch/historical_sales/source=kaggle/full/walmart_sales_full.parquet"
    )

    print("\nDone! Check Azure Portal → walmartdata → bronze container")

if __name__ == "__main__":
    run()