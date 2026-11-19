
import io
import pandas as pd
from azure.identity import AzureCliCredential
from azure.storage.filedatalake import DataLakeServiceClient

# Connect to Azure Data Lake
account_url = "https://stdementiadev001.dfs.core.windows.net"

service_client = DataLakeServiceClient(
    account_url=account_url,
    credential=AzureCliCredential()
)

# Locate the NHS PCDEM dataset
file_system = service_client.get_file_system_client("bronze")

file_client = file_system.get_file_client(
    "pcdem/pcdem-sicbl-age-sex-oct-2025.csv"
)

# Download the CSV into memory
csv_bytes = file_client.download_file().readall()

# Load into Pandas
df = pd.read_csv(io.BytesIO(csv_bytes), low_memory=False)

# Inspect the dataset
print("\nDATASET SHAPE:")
print(df.shape)

print("\nCOLUMN NAMES:")
print(df.columns.tolist())

print("\nFIRST 5 ROWS:")
print(df.head().to_string())

print("\nMISSING VALUES:")
print(df.isnull().sum().to_string())

print("\nDATA TYPES:")
print(df.dtypes.to_string())
print("\nUNIQUE MEASURES:")
print(sorted(df["Measure"].unique()))

print("\nNUMBER OF UNIQUE MEASURES:")
print(df["Measure"].nunique())


print("\nUNIQUE REPORTING DATES:")
print(df["ACH_DATE"].unique())

print("\nNUMBER OF SUB-ICBs:")
print(df["SUB_ICB_ODS_CODE"].nunique())

print("\nVALUE SUMMARY:")
print(df["Value"].describe())
print("\nREPORTING DATES:")
print(df["ACH_DATE"].value_counts().sort_index())