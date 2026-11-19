
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

def read_parquet(container, path):
    data = container.get_file_client(path).download_file().readall()
    return pd.read_parquet(io.BytesIO(data))

# 1. Read Silver fact source and Gold dimensions
pcdem = read_parquet(silver, "pcdem/pcdem_clean.parquet")

dim_sub_icb = read_parquet(
    gold, "dimensions/dim_sub_icb.parquet"
)

dim_date = read_parquet(
    gold, "dimensions/dim_date.parquet"
)

dim_demographic = read_parquet(
    gold, "dimensions/dim_demographic.parquet"
)

print("Silver PCDEM records:", len(pcdem))

# 2. Prepare reporting dates
pcdem["ACH_DATE"] = pd.to_datetime(pcdem["ACH_DATE"])
dim_date["Reporting_Date"] = pd.to_datetime(
    dim_date["Reporting_Date"]
)

# 3. Join Sub-ICB dimension
fact = pcdem.merge(
    dim_sub_icb[["Sub_ICB_Code_H", "Sub_ICB_Key"]],
    left_on="SUB_ICB_ODS_CODE",
    right_on="Sub_ICB_Code_H",
    how="left",
    validate="many_to_one"
)

# 4. Join Date dimension
fact = fact.merge(
    dim_date[["Reporting_Date", "Date_Key"]],
    left_on="ACH_DATE",
    right_on="Reporting_Date",
    how="left",
    validate="many_to_one"
)

# 5. Join Demographic dimension
fact = fact.merge(
    dim_demographic[
        ["Sex", "Age_Group", "Demographic_Key"]
    ],
    on=["Sex", "Age_Group"],
    how="left",
    validate="many_to_one"
)

# 6. Validate foreign keys
foreign_keys = [
    "Sub_ICB_Key",
    "Date_Key",
    "Demographic_Key"
]

if fact[foreign_keys].isna().any().any():
    print(fact[foreign_keys].isna().sum())
    raise ValueError("Unmatched dimension keys detected")

# 7. Validate row counts
if len(fact) != len(pcdem):
    raise ValueError("Fact row count mismatch")

# 8. Select final fact columns
fact_dementia = fact[
    [
        "Date_Key",
        "Sub_ICB_Key",
        "Demographic_Key",
        "Value"
    ]
].rename(columns={
    "Value": "Measure_Value"
})

# 9. Validate uniqueness and measures
grain = [
    "Date_Key",
    "Sub_ICB_Key",
    "Demographic_Key"
]

if fact_dementia.duplicated(subset=grain).any():
    raise ValueError("Duplicate fact grain detected")

if fact_dementia["Measure_Value"].isna().any():
    raise ValueError("Missing measure values detected")

if (fact_dementia["Measure_Value"] < 0).any():
    raise ValueError("Negative measure values detected")

print("\nGOLD FACT VALIDATION:")
print("Fact records:", len(fact_dementia))
print("Unique dates:", fact_dementia["Date_Key"].nunique())
print("Unique Sub-ICBs:", fact_dementia["Sub_ICB_Key"].nunique())
print(
    "Unique demographic groups:",
    fact_dementia["Demographic_Key"].nunique()
)
print("Duplicate fact records:",
      fact_dementia.duplicated(subset=grain).sum())

print("\nFIRST 5 ROWS:")
print(fact_dementia.head().to_string(index=False))

# 10. Convert to Parquet
buffer = io.BytesIO()

fact_dementia.to_parquet(
    buffer,
    index=False,
    engine="pyarrow"
)

# 11. Upload to Azure Gold
gold_file = gold.get_file_client(
    "facts/fact_dementia.parquet"
)

gold_file.upload_data(
    buffer.getvalue(),
    overwrite=True
)

print("\nSUCCESS: FactDementia uploaded to Azure Gold!")
