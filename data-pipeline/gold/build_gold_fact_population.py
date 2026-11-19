
import io
import pandas as pd
from azure.identity import AzureCliCredential
from azure.storage.filedatalake import DataLakeServiceClient

# Connect to Azure
service = DataLakeServiceClient(
    account_url="https://stdementiadev001.dfs.core.windows.net",
    credential=AzureCliCredential()
)

silver = service.get_file_system_client("silver")
gold = service.get_file_system_client("gold")

# Read MYE2 Silver dataset
data = silver.get_file_client(
    "mye2/mye2_clean.parquet"
).download_file().readall()

df = pd.read_parquet(io.BytesIO(data))

# Keep only Local Authorities matching our geographic lookup
geo_data = silver.get_file_client(
    "geography/geography_lookup.parquet"
).download_file().readall()

geo = pd.read_parquet(io.BytesIO(geo_data))

lad_codes = set(geo["Local_Authority_Code"])

fact_population = df[
    df["Geography_Code"].isin(lad_codes)
].copy()

# Select population measures
fact_population = fact_population[
    [
        "Geography_Code",
        "Total_Population",
        "Population_65_Plus"
    ]
].rename(columns={
    "Geography_Code": "Local_Authority_Code"
})

# Validate population data
if fact_population["Local_Authority_Code"].duplicated().any():
    raise ValueError("Duplicate Local Authority codes")

if fact_population.isna().any().any():
    raise ValueError("Missing population values")

if (
    fact_population["Population_65_Plus"]
    > fact_population["Total_Population"]
).any():
    raise ValueError("Population aged 65+ exceeds total population")

if len(fact_population) != len(lad_codes):
    raise ValueError("Local Authority coverage mismatch")

print("\nGOLD POPULATION VALIDATION:")
print("Local Authorities:", len(fact_population))
print("Duplicate Local Authorities:",
      fact_population["Local_Authority_Code"].duplicated().sum())
print("Missing values:", fact_population.isna().sum().sum())

print("\nFIRST 5 ROWS:")
print(fact_population.head().to_string(index=False))

# Convert to Parquet
buffer = io.BytesIO()

fact_population.to_parquet(
    buffer,
    index=False,
    engine="pyarrow"
)

# Upload to Gold
gold_file = gold.get_file_client(
    "facts/fact_population.parquet"
)

gold_file.upload_data(
    buffer.getvalue(),
    overwrite=True
)

print("\nSUCCESS: FactPopulation uploaded to Azure Gold!")
