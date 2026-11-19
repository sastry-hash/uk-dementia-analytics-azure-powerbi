
import io
import pandas as pd
from azure.identity import AzureCliCredential
from azure.storage.filedatalake import DataLakeServiceClient

# Connect to Azure Data Lake
service = DataLakeServiceClient(
    account_url="https://stdementiadev001.dfs.core.windows.net",
    credential=AzureCliCredential()
)

# Read PCDEM Silver dataset
silver = service.get_file_system_client("silver")

file_client = silver.get_file_client(
    "pcdem/pcdem_clean.parquet"
)

data = file_client.download_file().readall()
df = pd.read_parquet(io.BytesIO(data))

# Check required columns
required = ["Sex", "Age_Group"]

if not all(col in df.columns for col in required):
    raise ValueError("Missing demographic columns")

# Extract unique demographic combinations
dim_demographic = (
    df[["Sex", "Age_Group"]]
    .drop_duplicates()
    .sort_values(["Sex", "Age_Group"])
    .reset_index(drop=True)
)

# Validate missing values
if dim_demographic.isna().any().any():
    raise ValueError("Missing demographic values")

# Validate uniqueness
if dim_demographic.duplicated(
    subset=["Sex", "Age_Group"]
).any():
    raise ValueError("Duplicate demographic combinations")

# Generate surrogate key
dim_demographic.insert(
    0,
    "Demographic_Key",
    range(1, len(dim_demographic) + 1)
)

# Print validation results
print("\nGOLD DEMOGRAPHIC VALIDATION:")
print("Total demographic combinations:", len(dim_demographic))
print("Unique sex categories:", dim_demographic["Sex"].nunique())
print("Unique age groups:", dim_demographic["Age_Group"].nunique())
print("Duplicate combinations:",
      dim_demographic.duplicated(
          subset=["Sex", "Age_Group"]
      ).sum())

print("\nDEMOGRAPHIC DIMENSION:")
print(dim_demographic.to_string(index=False))

# Validate expected structure
if len(dim_demographic) != 18:
    raise ValueError(
        "Expected 18 demographic combinations"
    )

# Convert to Parquet
buffer = io.BytesIO()

dim_demographic.to_parquet(
    buffer,
    index=False,
    engine="pyarrow"
)

# Upload to Azure Gold
gold = service.get_file_system_client("gold")

gold_file = gold.get_file_client(
    "dimensions/dim_demographic.parquet"
)

gold_file.upload_data(
    buffer.getvalue(),
    overwrite=True
)

print("\nSUCCESS: DimDemographic uploaded to Azure Gold!")
