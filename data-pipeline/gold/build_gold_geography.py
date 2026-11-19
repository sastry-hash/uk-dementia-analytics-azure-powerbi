
import io
import pandas as pd
from azure.identity import AzureCliCredential
from azure.storage.filedatalake import DataLakeServiceClient

# Connect to Azure
service = DataLakeServiceClient(
    account_url="https://stdementiadev001.dfs.core.windows.net",
    credential=AzureCliCredential()
)

# Read PCDEM Silver data
silver = service.get_file_system_client("silver")

file_client = silver.get_file_client(
    "pcdem/pcdem_clean.parquet"
)

data = file_client.download_file().readall()
df = pd.read_parquet(io.BytesIO(data))

# Extract unique reporting dates
dim_date = pd.DataFrame({
    "Reporting_Date": pd.to_datetime(
        df["ACH_DATE"]
    ).drop_duplicates()
})

dim_date = dim_date.sort_values(
    "Reporting_Date"
).reset_index(drop=True)

# Create date attributes
dim_date["Date_Key"] = (
    dim_date["Reporting_Date"].dt.strftime("%Y%m%d").astype(int)
)

dim_date["Year"] = dim_date["Reporting_Date"].dt.year
dim_date["Month_Number"] = dim_date["Reporting_Date"].dt.month
dim_date["Month_Name"] = dim_date["Reporting_Date"].dt.strftime("%B")
dim_date["Year_Month"] = dim_date["Reporting_Date"].dt.strftime("%Y-%m")

# Arrange columns
dim_date = dim_date[
    [
        "Date_Key",
        "Reporting_Date",
        "Year",
        "Month_Number",
        "Month_Name",
        "Year_Month"
    ]
]

# Validate
if dim_date["Date_Key"].duplicated().any():
    raise ValueError("Duplicate Date Keys detected")

if dim_date["Reporting_Date"].isna().any():
    raise ValueError("Missing reporting dates detected")

print("\nGOLD DATE DIMENSION VALIDATION:")
print("Total reporting months:", len(dim_date))
print("Earliest date:", dim_date["Reporting_Date"].min())
print("Latest date:", dim_date["Reporting_Date"].max())
print("Duplicate dates:", dim_date["Date_Key"].duplicated().sum())

print("\nFIRST 5 ROWS:")
print(dim_date.head().to_string(index=False))

# Convert to Parquet
buffer = io.BytesIO()
dim_date.to_parquet(
    buffer,
    index=False,
    engine="pyarrow"
)

# Upload to Gold
gold = service.get_file_system_client("gold")

gold_file = gold.get_file_client(
    "dimensions/dim_date.parquet"
)

gold_file.upload_data(
    buffer.getvalue(),
    overwrite=True
)

print("\nSUCCESS: DimDate uploaded to Azure Gold!")
