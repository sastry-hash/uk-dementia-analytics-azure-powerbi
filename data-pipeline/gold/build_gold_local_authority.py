
import io
import pandas as pd
from azure.identity import AzureCliCredential
from azure.storage.filedatalake import DataLakeServiceClient

service = DataLakeServiceClient(
    account_url="https://stdementiadev001.dfs.core.windows.net",
    credential=AzureCliCredential()
)

silver = service.get_file_system_client("silver")
gold = service.get_file_system_client("gold")

# Read geographic lookup
data = silver.get_file_client(
    "geography/geography_lookup.parquet"
).download_file().readall()

df = pd.read_parquet(io.BytesIO(data))

# Extract unique Local Authorities
dim_lad = df[
    ["Local_Authority_Code", "Local_Authority_Name"]
].drop_duplicates().copy()

# Validate unique codes
if dim_lad["Local_Authority_Code"].duplicated().any():
    raise ValueError("Conflicting Local Authority mappings")

if dim_lad.isna().any().any():
    raise ValueError("Missing Local Authority values")

# Generate surrogate keys
dim_lad = dim_lad.sort_values(
    "Local_Authority_Code"
).reset_index(drop=True)

dim_lad.insert(
    0,
    "Local_Authority_Key",
    range(1, len(dim_lad) + 1)
)

# Validate
print("\nGOLD LOCAL AUTHORITY VALIDATION:")
print("Total Local Authorities:", len(dim_lad))
print(
    "Duplicate codes:",
    dim_lad["Local_Authority_Code"].duplicated().sum()
)

print("\nFIRST 5 ROWS:")
print(dim_lad.head().to_string(index=False))

# Convert to Parquet
buffer = io.BytesIO()
dim_lad.to_parquet(buffer, index=False, engine="pyarrow")

# Upload to Gold
gold_file = gold.get_file_client(
    "dimensions/dim_local_authority.parquet"
)

gold_file.upload_data(
    buffer.getvalue(),
    overwrite=True
)

print("\nSUCCESS: DimLocalAuthority uploaded to Azure Gold!")
