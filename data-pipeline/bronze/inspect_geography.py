
import io
import pandas as pd
from azure.identity import AzureCliCredential
from azure.storage.filedatalake import DataLakeServiceClient

# 1. Connect to Azure Data Lake
service_client = DataLakeServiceClient(
    account_url="https://stdementiadev001.dfs.core.windows.net",
    credential=AzureCliCredential()
)

# 2. Access Bronze container
bronze = service_client.get_file_system_client("bronze")

# 3. Find geographic lookup CSV
file_client = bronze.get_file_client(
    "LSOA_SUB_ICB/LSOA_(2021)_to_SICBL_to_ICB_to_LAD_(April_2023)_Lookup_in_EN.csv"
)

# 4. Download CSV into memory
csv_bytes = file_client.download_file().readall()

# 5. Load as text to preserve geographic codes
df = pd.read_csv(
    io.BytesIO(csv_bytes),
    dtype=str,
    low_memory=False
)

# 6. Inspect dataset
print("\nDATASET SHAPE:")
print(df.shape)

print("\nCOLUMN NAMES:")
print(df.columns.tolist())

print("\nFIRST 5 ROWS:")
print(df.head().to_string(index=False))

print("\nMISSING VALUES:")
print(df.isna().sum().to_string())

print("\nDUPLICATE ROWS:")
print(df.duplicated().sum())


print("\nGEOGRAPHIC RELATIONSHIP VALIDATION:")

print("Total LSOAs:", df["LSOA21CD"].nunique())
print("Total Sub-ICBs:", df["SICBL23CD"].nunique())
print("Total ICBs:", df["ICB23CD"].nunique())
print("Total Local Authorities:", df["LAD23CD"].nunique())

print(
    "LSOAs mapped to multiple Sub-ICBs:",
    (df.groupby("LSOA21CD")["SICBL23CD"].nunique() > 1).sum()
)

print(
    "LSOAs mapped to multiple Local Authorities:",
    (df.groupby("LSOA21CD")["LAD23CD"].nunique() > 1).sum()
)

print(
    "Local Authorities spanning multiple Sub-ICBs:",
    (df.groupby("LAD23CD")["SICBL23CD"].nunique() > 1).sum()
)

print(
    "Sub-ICBs spanning multiple Local Authorities:",
    (df.groupby("SICBL23CD")["LAD23CD"].nunique() > 1).sum()
)
