
import io
import pandas as pd

from azure.identity import AzureCliCredential
from azure.storage.filedatalake import DataLakeServiceClient

# ==================================================
# 1. CONNECT TO AZURE DATA LAKE STORAGE
# ==================================================

service = DataLakeServiceClient(
    account_url="https://stdementiadev001.dfs.core.windows.net",
    credential=AzureCliCredential()
)

silver = service.get_file_system_client("silver")
gold = service.get_file_system_client("gold")


def read_parquet(container, path):
    file_client = container.get_file_client(path)
    data = file_client.download_file().readall()
    return pd.read_parquet(io.BytesIO(data))


# ==================================================
# 2. READ SILVER POPULATION DATA
# ==================================================

population = read_parquet(
    silver,
    "mye2/mye2_clean.parquet"
)

print("Silver population records:", len(population))


# ==================================================
# 3. READ GOLD LOCAL AUTHORITY DIMENSION
# ==================================================

dim_lad = read_parquet(
    gold,
    "dimensions/dim_local_authority.parquet"
)

print("Local Authority dimension records:", len(dim_lad))


# ==================================================
# 4. VALIDATE DIMENSION KEYS
# ==================================================

if dim_lad["Local_Authority_Code"].duplicated().any():
    raise ValueError("Duplicate Local Authority codes")

if dim_lad["Local_Authority_Key"].duplicated().any():
    raise ValueError("Duplicate Local Authority surrogate keys")


# ==================================================
# 5. JOIN POPULATION WITH LOCAL AUTHORITY
# ==================================================

fact = population.merge(
    dim_lad[
        [
            "Local_Authority_Key",
            "Local_Authority_Code"
        ]
    ],
    left_on="Geography_Code",
    right_on="Local_Authority_Code",
    how="inner",
    validate="one_to_one"
)

print("Matched population records:", len(fact))


# ==================================================
# 6. VALIDATE GEOGRAPHIC COVERAGE
# ==================================================

if len(fact) != len(dim_lad):
    raise ValueError(
        "Population and Local Authority coverage mismatch"
    )


# ==================================================
# 7. BUILD FINAL FACT TABLE
# ==================================================

fact_population = fact[
    [
        "Local_Authority_Key",
        "Total_Population",
        "Population_65_Plus"
    ]
].copy()

fact_population["Local_Authority_Key"] = (
    fact_population["Local_Authority_Key"].astype(int)
)

fact_population["Total_Population"] = pd.to_numeric(
    fact_population["Total_Population"],
    errors="raise"
)

fact_population["Population_65_Plus"] = pd.to_numeric(
    fact_population["Population_65_Plus"],
    errors="raise"
)


# ==================================================
# 8. DATA QUALITY VALIDATION
# ==================================================

if len(fact_population) != 296:
    raise ValueError("Expected 296 Local Authorities")

if fact_population["Local_Authority_Key"].duplicated().any():
    raise ValueError("Duplicate Local Authority keys")

if fact_population.isna().any().any():
    raise ValueError("Missing values detected")

if (
    fact_population[
        ["Total_Population", "Population_65_Plus"]
    ] < 0
).any().any():
    raise ValueError("Negative population values")

if (
    fact_population["Population_65_Plus"]
    > fact_population["Total_Population"]
).any():
    raise ValueError(
        "Population aged 65+ exceeds total population"
    )


# ==================================================
# 9. DISPLAY VALIDATION RESULTS
# ==================================================

print("\nGOLD POPULATION FACT VALIDATION")

print("Fact records:", len(fact_population))

print(
    "Unique Local Authorities:",
    fact_population["Local_Authority_Key"].nunique()
)

print(
    "Duplicate keys:",
    fact_population["Local_Authority_Key"].duplicated().sum()
)

print(
    "Missing values:",
    fact_population.isna().sum().sum()
)

print("\nFINAL COLUMNS:")
print(fact_population.columns.tolist())

print("\nFIRST FIVE ROWS:")
print(fact_population.head().to_string(index=False))


# ==================================================
# 10. CONVERT TO PARQUET
# ==================================================

buffer = io.BytesIO()

fact_population.to_parquet(
    buffer,
    index=False,
    engine="pyarrow"
)


# ==================================================
# 11. UPLOAD TO AZURE GOLD
# ==================================================

gold_file = gold.get_file_client(
    "facts/fact_population.parquet"
)

gold_file.upload_data(
    buffer.getvalue(),
    overwrite=True
)

print("\nSUCCESS: FactPopulation updated in Azure Gold!")
