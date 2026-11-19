
import io
import pandas as pd
from azure.identity import AzureCliCredential
from azure.storage.filedatalake import DataLakeServiceClient

# 1. Connect to Azure
account_url = "https://stdementiadev001.dfs.core.windows.net"

service_client = DataLakeServiceClient(
    account_url=account_url,
    credential=AzureCliCredential()
)

# 2. Read the Bronze PCDEM CSV
bronze = service_client.get_file_system_client("bronze")

file_client = bronze.get_file_client(
    "pcdem/pcdem-sicbl-age-sex-oct-2025.csv"
)

csv_bytes = file_client.download_file().readall()
df = pd.read_csv(io.BytesIO(csv_bytes), dtype=str)

print("Bronze records:", len(df))

# 3. Clean column names and text values
df.columns = df.columns.str.strip()

for col in df.columns:
    df[col] = df[col].str.strip()

# 4. Convert reporting dates
df["ACH_DATE"] = pd.to_datetime(
    df["ACH_DATE"],
    format="%d-%b-%y",
    errors="raise"
)

# 5. Convert Value to numeric
df["Value"] = pd.to_numeric(
    df["Value"],
    errors="raise"
)

# 6. Extract sex and age group
parts = df["Measure"].str.extract(
    r"^(ALL|MALE|FEMALE)_AGED_(65_69|70_74|75_79|80_84|85_89|90_PLUS)$"
)

if parts.isna().any().any():
    raise ValueError("Unexpected Measure codes found")

df["Sex"] = parts[0]
df["Age_Group"] = parts[1].str.replace("_", "-", regex=False)

# 7. Validate the dataset
key_columns = [
    "ACH_DATE",
    "SUB_ICB_ODS_CODE",
    "Measure"
]

duplicates = df.duplicated(subset=key_columns).sum()

if duplicates:
    raise ValueError(f"Found {duplicates} duplicate records")

if df["Value"].isna().any() or (df["Value"] < 0).any():
    raise ValueError("Invalid values detected")

print("Duplicate records:", duplicates)
print("Missing values:", df.isna().sum().sum())
print("Reporting months:", df["ACH_DATE"].nunique())
print("Unique Sub-ICBs:", df["SUB_ICB_ODS_CODE"].nunique())

# 8. Prepare Parquet output in memory
parquet_buffer = io.BytesIO()
df.to_parquet(parquet_buffer, index=False, engine="pyarrow")
parquet_buffer.seek(0)

print("Silver Parquet prepared successfully")

# 9. Upload to Azure Silver
silver = service_client.get_file_system_client("silver")

silver_file = silver.get_file_client(
    "pcdem/pcdem_clean.parquet"
)

silver_file.upload_data(
    parquet_buffer.getvalue(),
    overwrite=True
)

print("SUCCESS: Silver PCDEM Parquet uploaded to Azure!")
