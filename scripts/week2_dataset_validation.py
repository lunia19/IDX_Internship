# IDX Exchange Data Analyst Internship
# Week 2 – Dataset Structuring, Validation, and Initial EDA

# Purpose:
    # This script inspects the combined Residential listing and sold datasets
    # created in Week 1. It checks dataset structure, data types, missing values,
    # property type consistency, and numeric field summaries.

# Author: Palak Lunia

import pandas as pd 
from pathlib import Path 

# 1. Project Paths

BASE_DIR = Path("/Users/palaklunia/Desktop/IDX_Internship")

WEEK1_DIR = BASE_DIR / "outputs" / "week1"
OUTPUT_DIR = BASE_DIR / "outputs" / "week2"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

listing_file = WEEK1_DIR / "combined_listing_residential.csv"
sold_file = WEEK1_DIR / "combined_sold_residential.csv"

# 2. Load Datasets 
# using .dtypes -> this lists the data type of every column 
print("Loading week 1 residential datasets")
print("-" * 60)

listings = pd.read_csv(listing_file, low_memory=False)
sold = pd.read_csv(sold_file, low_memory=False)

print(f"Listings dataset loaded: {listings.shape[0]:,} rows, {listings.shape[1]:,} columns")
print(f"Sold dataset xxloaded : {sold.shape[0]:,} rows, {sold.shape[1]:,} columns")

# 3. Dataset Structure Summary 
    # In order to identify number of rows and columns 

structure_summary = pd.DataFrame(
    [
        {
            "dataset" : "listings", 
            "rows" : listings.shape[0],
            "columns" : listings.shape[1],
            "duplicate_rows" : listings.duplicated().sum()
        },
        {
            "dataset" : "sold",
            "rows" : sold.shape[0],
            "columns" : sold.shape[1],
            "duplicate_rows" : sold.duplicated().sum()
        } 
    ] 
)

    


print("Dataset Structure Summary")
print("-" * 60)
print(structure_summary)
print()

# 4. Data Type Summary 
    # To check what type of data each column contains 

listing_dtypes = ( # this function returns the data type for each column in the listings data set
    listings.dtypes.reset_index()
)

listing_dtypes.columns = ["column_name", "data_type"] # this structure will make the output easier to understand
listing_dtypes["dataset"] = "listings" # creates new column called dataset = listings 

sold_dtypes = (sold.dtypes.reset_index())

sold_dtypes.columns = ["column_name", "data_type"]
sold_dtypes["dataset"] = "sold"

dtype_summary = pd.concat( # pd.concat combines two tables together 
    [listing_dtypes, sold_dtypes],
    ignore_index=True
)

# 5. Property Type Check 

listing_property_type_check = (
    listings["PropertyType"].value_counts(dropna=False).reset_index()
)

listing_property_type_check.columns = ["PropertyType", "row_count"]

sold_property_type_check = (
    sold["PropertyType"].value_counts(dropna=False).reset_index()
)

sold_property_type_check.columns = ["PropertyType", "row_count"]

print("Property Type Check")
print("-" * 60)
print("Listings:")
print(listing_property_type_check)
print()
print("Sold:")
print(sold_property_type_check)
print()

# 6. Missing Value Summary 
    # calculate missing counts and percentages per column 

def create_missing_summary(df, dataset_name):
    # creates a missing value summary for every column.
    # includes missing count, missing percentage, and >90% missing flag.
    
    summary = pd.DataFrame(
        {"column_name" : df.columns,
         "missing_count" : df.isna().sum().values,
         "total_rows" : len(df)
        }
    )

    summary["missing_percent"] = round(
        summary["missing_count"] / summary["total_rows"] * 100,
        2
    )

    # flag columns with >90% missing values 
    summary["above_90_percent_missing"] = summary["missing_percent"] > 90
    summary["dataset"] = dataset_name


    summary = summary.sort_values(
        by = "missing_percent",
        ascending=False
    )

    return summary 

listing_null_summary = create_missing_summary(listings, "listings")
sold_null_summary = create_missing_summary(sold, "sold")

print("Top 10 Missing Columns - Listings")
print("-" * 60)
print(listing_null_summary.head(10))
print()

print("Top 10 Missing Columns - Sold")
print("-" * 60)
print(sold_null_summary.head(10))
print()

# 7. Numeric Distribution Summary 

numeric_fields = [
    "ClosePrice",
    "ListingPrice",
    "OriginalListPrice",
    "LivingArea",
    "LotSizeAcres",
    "BedroomsTotal",
    "BathroomsTotalInteger",
    "DaysOnMarket",
    "YearBuilt"
]

def create_numeric_summary(df, dataset_name, fields):
    # creates numeric summaries for selected fields if they exist in the dataset.

    available_fields = [field for field in fields if field in df.columns]

    numeric_df = df[available_fields].copy()

    for field in available_fields:
        numeric_df[field] = pd.to_numeric(numeric_df[field], errors="coerce")

    summary = numeric_df.describe(
        percentiles = [0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99]
    ).T.reset_index()

    summary = summary.rename(columns={
        "index" : "fields",
        "50%" : "median"
    })

    summary["dataset"] = dataset_name

    return summary 

listing_numeric_summary = create_numeric_summary(
    listings,
    "listings",
    numeric_fields
)

sold_numeric_summary = create_numeric_summary(
    sold,
    "sold",
    numeric_fields
)

print("Sold Numeric Summary")
print("-" * 60)
print(sold_numeric_summary)
print()

print("Listing Numeric Summary")
print("-" * 60)
print(listing_numeric_summary)
print()

# 8. Save week 2 Output Files

structure_summary.to_csv(
    OUTPUT_DIR / "week2_dataset_structure_summary.csv",
    index = False 
)

dtype_summary.to_csv(
    OUTPUT_DIR / "week2_dtype_summary.csv",
    index = False
)

listing_null_summary.to_csv(
    OUTPUT_DIR / "week2_listing_null_summary.csv",
    index = False
)

sold_null_summary.to_csv(
    OUTPUT_DIR / "week2_sold_null_summary.csv",
    index = False
)

listing_numeric_summary.to_csv(
    OUTPUT_DIR / "week2_listing_numeric_summary.csv",
    index = False
)

listing_numeric_summary.to_csv(
    OUTPUT_DIR / "week2_sold_numeric_summary.csv",
    index = False
)

sold_numeric_summary.to_csv(
    OUTPUT_DIR / "week2_listing_property_type_check.csv",
    index = False 
)

listing_property_type_check.to_csv(
    OUTPUT_DIR / "week2_sold_property_type_check.csv",
    index = False
)

# 9. Final Confirmation 

print("Week 2 Output Files Created")
print("-" * 60)

for file in OUTPUT_DIR.glob("*.csv"):
    print(f"Saved: {file}")

print()
print("Week 2 dataset validation and initial EDA complete.")

