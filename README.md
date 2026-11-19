# uk-dementia-analytics-azure-powerbi
# UK Dementia Analytics — Azure Data Engineering & Power BI

## Project Overview

This project implements an end-to-end cloud data engineering and business intelligence solution to analyse dementia-related indicators and population demographics across England.

The solution integrates publicly available NHS dementia indicator data, Office for National Statistics (ONS) population estimates, and geographical reference datasets.

Using Microsoft Azure Data Lake Storage Gen2 and Python, the project implements a Medallion Architecture (Bronze, Silver and Gold) to ingest, clean, validate and transform data for analytical reporting.

The processed datasets are used in Power BI to create an interactive four-page dashboard covering dementia indicators, NHS regional comparisons, age and gender distributions, and local authority population demographics.

## Technologies Used

- **Cloud Platform:** Microsoft Azure, Azure Data Lake Storage Gen2
- **Programming:** Python, Pandas
- **Data Engineering:** ETL, Medallion Architecture, CSV, Parquet
- **Data Modelling:** Fact Tables, Dimension Tables, Star Schema Design
- **Business Intelligence:** Microsoft Power BI, DAX, Power Query
- **Version Control:** Git and GitHub

## Data Sources

**1. NHS Primary Care Dementia Data (PCDEM)**

- 24,804 records
- 106 NHS Sub-ICBs
- 13 reporting months, October 2024–October 2025
- Dementia indicators categorised by age and sex

**2. ONS Population Estimates (MYE2)**

- Population estimates by local authority
- Total population and age-specific population counts
- Used to analyse population demographics and residents aged 65+

**3. Geographical Lookup Dataset**

- NHS Sub-ICB, ICB and local authority reference information
- Supports geographical standardisation and analysis

## Data Architecture

The project follows a three-layer Medallion Architecture.

### Bronze Layer — Raw Data Ingestion

- Ingested source CSV files into Azure Data Lake Storage Gen2.
- Preserved the original data structure.
- Organised source datasets into dedicated storage paths.

### Silver Layer — Data Cleaning and Validation

- Standardised data types and column structures.
- Checked missing values and duplicate records.
- Validated geographical identifiers and reporting dates.
- Produced cleaned datasets in Parquet format.

### Gold Layer — Analytical Data Modelling

- Prepared structured fact and dimension tables.
- Implemented a dimensional model for analytical reporting.
- Established relationships between fact and dimension tables in Power BI.
- Developed DAX measures for KPIs and interactive analysis.

## Power BI Dashboard

The dashboard contains four analytical pages.

### Page 1 — Dementia Overview

- Selected-period dementia indicator
- NHS Sub-ICB coverage
- Dementia indicators by age group
- Monthly reporting trends
- Top 10 NHS ICBs

### Page 2 — Regional Analysis

- NHS ICB comparisons
- Regional indicator rankings
- Monthly trends by ICB
- Interactive year and geographical filters

### Page 3 — Age & Gender Analysis

- Male and female dementia indicators
- Age-group distributions
- Monthly trends by sex
- Interactive demographic comparisons
### Page 4 — Population Analysis

- Total population
- Population aged 65+
- Percentage of population aged 65+
- Top 10 local authorities by population
- Local authority demographic comparisons

### Data Quality and Limitations

Data validation includes duplicate detection, missing-value checks and geographical identifier verification.

Dementia indicators and population estimates use different geographical structures. The dashboard therefore presents NHS dementia indicators and local authority population statistics separately rather than calculating an unsupported dementia prevalence rate.

Population reference periods and indicator definitions should be verified against the original source documentation before interpreting results.

Project Purpose

This project demonstrates practical experience in cloud data engineering, data transformation, dimensional modelling, analytical reporting and dashboard development using Azure, Python and Power BI.
