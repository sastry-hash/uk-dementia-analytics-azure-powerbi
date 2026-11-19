
import io
import pandas as pd
from azure.identity import AzureCliCredential
from azure.storage.filedatalake import DataLakeServiceClient

# 1. Connect to Azure Data Lake
service_client = DataLakeServiceClient(
    account_url="https://stdementiadev001.dfs.core.windows.net",
    credential=AzureCliCredential()
)

# 2. Read geographic lookup from Bronze
bronze = service_client.get_file_system_client("bronze")

file_client = bronze.get_file_client(
    "LSOA_SUB_ICB/LSOA_(2021)_to_SICBL_to_ICB_to_LAD_(April_2023)_Lookup_in_EN.csv"
)

csv_bytes = file_client.download_file().readall()

df = pd.read_csv(
    io.BytesIO(csv_bytes),
    dtype=str,
    low_memory=False
)

print("Bronze records:", len(df))

# 3. Clean column names and text
df.columns = df.columns.str.strip()

for col in df.columns:
    df[col] = df[col].str.strip()

# 4. Keep relevant geographic columns
df = df[
    [
        "LSOA21CD",
        "LSOA21NM",
        "SICBL23CD",
        "SICBL23CDH",
        "SICBL23NM",
        "ICB23CD",
        "ICB23CDH",
        "ICB23NM",
        "LAD23CD",
        "LAD23NM"
    ]
].copy()

# 5. Rename columns for Silver
df = df.rename(columns={
    "LSOA21CD": "LSOA_Code",
    "LSOA21NM": "LSOA_Name",
    "SICBL23CD": "Sub_ICB_Code",
    "SICBL23CDH": "Sub_ICB_Code_H",
    "SICBL23NM": "Sub_ICB_Name",
    "ICB23CD": "ICB_Code",
    "ICB23CDH": "ICB_Code_H",
    "ICB23NM": "ICB_Name",
    "LAD23CD": "Local_Authority_Code",
    "LAD23NM": "Local_Authority_Name"
})

# 6. Add geographic reference year
df["Geography_Reference_Year"] = 2023

# 7. Validate missing values
if df.isna().any().any():
    raise ValueError("Missing geographic values detected")

# 8. Validate unique LSOA mappings
if df["LSOA_Code"].duplicated().any():
    raise ValueError("Duplicate LSOA mappings detected")

# 9. Validate Sub-ICB to ICB relationship
sub_icb_icb = (
    df.groupby("Sub_ICB_Code")["ICB_Code"]
    .nunique()
)

if (sub_icb_icb > 1).any():
    raise ValueError("Sub-ICB maps to multiple ICBs")

# 10. Print validation results
print("\nSILVER VALIDATION:")
print("Total LSOAs:", df["LSOA_Code"].nunique())
print("Total Sub-ICBs:", df["Sub_ICB_Code"].nunique())
print("Total ICBs:", df["ICB_Code"].nunique())
print(
    "Total Local Authorities:",
    df["Local_Authority_Code"].nunique()
)
print("Duplicate LSOAs:", df["LSOA_Code"].duplicated().sum())
print("Missing values:", df.isna().sum().sum())

# 11. Convert to Parquet
parquet_buffer = io.BytesIO()

df.to_parquet(
    parquet_buffer,
    index=False,
    engine="pyarrow"
)

# 12. Upload to Azure Silver
silver = service_client.get_file_system_client("silver")

silver_file = silver.get_file_client(
    "geography/geography_lookup.parquet"
)

silver_file.upload_data(
    parquet_buffer.getvalue(),
    overwrite=True
)

print("\nSUCCESS: Geographic lookup uploaded to Silver!")
