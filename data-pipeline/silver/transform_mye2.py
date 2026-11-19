
import io
import pandas as pd
from azure.identity import AzureCliCredential
from azure.storage.filedatalake import DataLakeServiceClient

# 1. Connect to Azure
service_client = DataLakeServiceClient(
    account_url="https://stdementiadev001.dfs.core.windows.net",
    credential=AzureCliCredential()
)

# 2. Read MYE2 from Bronze
bronze = service_client.get_file_system_client("bronze")
file_client = bronze.get_file_client("mye2/mye2.csv")

csv_bytes = file_client.download_file().readall()
df = pd.read_csv(io.BytesIO(csv_bytes), dtype=str)

print("Bronze records:", len(df))

# 3. Clean column names and text
df.columns = df.columns.str.strip()

for col in ["Code", "Name", "Geography"]:
    df[col] = df[col].str.strip()

# 4. Convert population columns to numeric
age_columns = [str(age) for age in range(90)] + ["90+"]
numeric_columns = ["All ages"] + age_columns

for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors="raise")

# 5. Validate population values
if df[numeric_columns].isna().any().any():
    raise ValueError("Missing population values detected")

if (df[numeric_columns] < 0).any().any():
    raise ValueError("Negative population values detected")

if df["Code"].isna().any() or df["Code"].duplicated().any():
    raise ValueError("Missing or duplicate geographic codes")

# 6. Validate population totals
age_sum = df[age_columns].sum(axis=1)

if not age_sum.eq(df["All ages"]).all():
    raise ValueError("Population totals do not match")

# 7. Calculate population aged 65+
age_65_plus = [str(age) for age in range(65, 90)] + ["90+"]

df["Population_65_Plus"] = df[age_65_plus].sum(axis=1)
df["Total_Population"] = df["All ages"]

# 8. Rename geographic columns
df = df.rename(columns={
    "Code": "Geography_Code",
    "Name": "Geography_Name",
    "Geography": "Geography_Type"
})

print("Duplicate geography codes:", df["Geography_Code"].duplicated().sum())
print("Population validation: PASSED")
print("Records processed:", len(df))

# 9. Convert to Parquet
parquet_buffer = io.BytesIO()
df.to_parquet(parquet_buffer, index=False, engine="pyarrow")

print("Silver Parquet prepared successfully")

# 10. Upload to Azure Silver
silver = service_client.get_file_system_client("silver")

silver_file = silver.get_file_client(
    "mye2/mye2_clean.parquet"
)

silver_file.upload_data(
    parquet_buffer.getvalue(),
    overwrite=True
)

print("SUCCESS: MYE2 Silver Parquet uploaded to Azure!")
