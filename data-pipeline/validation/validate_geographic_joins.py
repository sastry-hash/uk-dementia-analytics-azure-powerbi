
import io
import pandas as pd
from azure.identity import AzureCliCredential
from azure.storage.filedatalake import DataLakeServiceClient

# Connect to Azure Silver
service = DataLakeServiceClient(
    account_url="https://stdementiadev001.dfs.core.windows.net",
    credential=AzureCliCredential()
)

silver = service.get_file_system_client("silver")

def read_parquet(path):
    data = silver.get_file_client(path).download_file().readall()
    return pd.read_parquet(io.BytesIO(data))

# Read all three Silver datasets
pcdem = read_parquet("pcdem/pcdem_clean.parquet")
mye2 = read_parquet("mye2/mye2_clean.parquet")
geo = read_parquet("geography/geography_lookup.parquet")

# Compare geographic codes
pcdem_codes = set(pcdem["SUB_ICB_ODS_CODE"].dropna())
sub_icb_codes = set(geo["Sub_ICB_Code_H"].dropna())

mye2_codes = set(mye2["Geography_Code"].dropna())
lad_codes = set(geo["Local_Authority_Code"].dropna())

print("\nGEOGRAPHIC JOIN VALIDATION:")

print("PCDEM Sub-ICB codes:", len(pcdem_codes))
print("Lookup Sub-ICB codes:", len(sub_icb_codes))
print("Matching Sub-ICB codes:", len(pcdem_codes & sub_icb_codes))
print("Unmatched PCDEM codes:", sorted(pcdem_codes - sub_icb_codes))

print("\nMYE2 geography codes:", len(mye2_codes))
print("Lookup Local Authority codes:", len(lad_codes))
print("Matching Local Authority codes:", len(mye2_codes & lad_codes))
print("Unmatched lookup LAD codes:", sorted(lad_codes - mye2_codes))
