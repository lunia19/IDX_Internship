
# IDX Exchange Data Analyst Internship
# Week 1 – Monthly Dataset Aggregation

# Purpose:
# This script combines all monthly CRMLS Listing and Sold CSV files from
# January 2024 through the latest available month into two combined datasets.

# It then filters both datasets to PropertyType == 'Residential' and saves
# the results as new CSV files.

# Author: Palak Lunia


import pandas as pd
from pathlib import Path
import re



# 1. SET PROJECT PATHS


BASE_DIR = Path("/Users/palaklunia/Desktop/IDX_Internship")

RAW_DIR = BASE_DIR / "raw_csv"
LISTING_DIR = RAW_DIR / "CRMLSListing"
SOLD_DIR = RAW_DIR / "CRMLSSold"

OUTPUT_DIR = BASE_DIR / "outputs" / "week1"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# 2. CHECK THAT REQUIRED FOLDERS EXIST

if not BASE_DIR.exists():
    raise FileNotFoundError(f"Base folder not found: {BASE_DIR}")

if not RAW_DIR.exists():
    raise FileNotFoundError(f"Raw CSV folder not found: {RAW_DIR}")

if not LISTING_DIR.exists():
    raise FileNotFoundError(f"Listing folder not found: {LISTING_DIR}")

if not SOLD_DIR.exists():
    raise FileNotFoundError(f"Sold folder not found: {SOLD_DIR}")


print("PROJECT FOLDER CHECK")
print("-" * 60)
print(f"Base folder    : {BASE_DIR}")
print(f"Raw CSV folder : {RAW_DIR}")
print(f"Listing folder : {LISTING_DIR}")
print(f"Sold folder    : {SOLD_DIR}")
print(f"Output folder  : {OUTPUT_DIR}")
print()


# 3. FIND LISTING AND SOLD CSV FILES

listing_files = sorted([
    file for file in LISTING_DIR.glob("*.csv")
    if not file.name.startswith(".")
])

sold_files = sorted([
    file for file in SOLD_DIR.glob("*.csv")
    if not file.name.startswith(".")
])

print("WEEK 1 FILE DISCOVERY")
print("-" * 60)
print(f"Listing files found : {len(listing_files)}")
print(f"Sold files found    : {len(sold_files)}")
print()

if len(listing_files) == 0:
    raise FileNotFoundError("No listing CSV files found in CRMLSListing folder.")

if len(sold_files) == 0:
    raise FileNotFoundError("No sold CSV files found in CRMLSSold folder.")


# 4. FUNCTION TO EXTRACT YEAR-MONTH FROM FILE NAME

def extract_year_month(filename):
  
   # Extract YYYYMM from filenames such as:
   # CRMLSListing202401.csv
   # CRMLSSold202405_filled.csv


    match = re.search(r"20\d{4}", filename)

    if match:
        return match.group(0)

    return None


# 5. FUNCTION TO LOAD AND COMBINE MONTHLY FILES

def load_and_combine(files, dataset_name):
    
    # Loads multiple monthly CSV files and combines them into one dataset.

   # Adds:
   # - source_file: original CSV file name
   # - source_year_month: month extracted from file name
    

    monthly_dataframes = []
    row_count_log = []

    print(f"LOADING {dataset_name.upper()} FILES")
    print("-" * 60)

    for file in files:
        year_month = extract_year_month(file.name)

        print(f"Loading: {file.name}")

        df = pd.read_csv(file, low_memory=False)

        rows_before = len(df)
        cols_before = df.shape[1]

        df["source_file"] = file.name
        df["source_year_month"] = year_month

        monthly_dataframes.append(df)

        row_count_log.append({
            "dataset": dataset_name,
            "file_name": file.name,
            "year_month": year_month,
            "rows_before_concatenation": rows_before,
            "columns_before_concatenation": cols_before
        })

    combined_df = pd.concat(
        monthly_dataframes,
        ignore_index=True,
        sort=False
    )

    print()
    print(f"{dataset_name} files combined successfully.")
    print(f"{dataset_name} total rows after concatenation: {len(combined_df):,}")
    print(f"{dataset_name} total columns after concatenation: {combined_df.shape[1]:,}")
    print()

    row_count_log_df = pd.DataFrame(row_count_log)

    return combined_df, row_count_log_df


# 6. LOAD AND COMBINE LISTING AND SOLD FILES

listing_all, listing_log = load_and_combine(listing_files, "listings")
sold_all, sold_log = load_and_combine(sold_files, "sold")


# 7. CHECK PROPERTY TYPE COUNTS BEFORE FILTERING

print("PROPERTY TYPE COUNTS BEFORE RESIDENTIAL FILTER")
print("-" * 60)

if "PropertyType" not in listing_all.columns:
    raise KeyError("PropertyType column not found in listing dataset.")

if "PropertyType" not in sold_all.columns:
    raise KeyError("PropertyType column not found in sold dataset.")


listing_property_counts = (
    listing_all["PropertyType"]
    .value_counts(dropna=False)
    .reset_index()
)

listing_property_counts.columns = ["PropertyType", "row_count"]


sold_property_counts = (
    sold_all["PropertyType"]
    .value_counts(dropna=False)
    .reset_index()
)

sold_property_counts.columns = ["PropertyType", "row_count"]


print("Listings PropertyType counts:")
print(listing_property_counts)
print()

print("Sold PropertyType counts:")
print(sold_property_counts)
print()


# 8. FILTER TO RESIDENTIAL ONLY

listing_rows_before_filter = len(listing_all)
sold_rows_before_filter = len(sold_all)

listing_residential = listing_all[
    listing_all["PropertyType"] == "Residential"
].copy()

sold_residential = sold_all[
    sold_all["PropertyType"] == "Residential"
].copy()

listing_rows_after_filter = len(listing_residential)
sold_rows_after_filter = len(sold_residential)

listing_rows_removed = listing_rows_before_filter - listing_rows_after_filter
sold_rows_removed = sold_rows_before_filter - sold_rows_after_filter


print("RESIDENTIAL FILTER SUMMARY")
print("-" * 60)

print(f"Listing rows before Residential filter : {listing_rows_before_filter:,}")
print(f"Listing rows after Residential filter  : {listing_rows_after_filter:,}")
print(f"Listing rows removed                   : {listing_rows_removed:,}")
print()

print(f"Sold rows before Residential filter    : {sold_rows_before_filter:,}")
print(f"Sold rows after Residential filter     : {sold_rows_after_filter:,}")
print(f"Sold rows removed                      : {sold_rows_removed:,}")
print()


# 9. CREATE FILTER SUMMARY TABLE

filter_summary = pd.DataFrame([
    {
        "dataset": "listings",
        "rows_before_residential_filter": listing_rows_before_filter,
        "rows_after_residential_filter": listing_rows_after_filter,
        "rows_removed": listing_rows_removed,
        "residential_share_percent": round(
            listing_rows_after_filter / listing_rows_before_filter * 100, 2
        )
    },
    {
        "dataset": "sold",
        "rows_before_residential_filter": sold_rows_before_filter,
        "rows_after_residential_filter": sold_rows_after_filter,
        "rows_removed": sold_rows_removed,
        "residential_share_percent": round(
            sold_rows_after_filter / sold_rows_before_filter * 100, 2
        )
    }
])


# 10. SAVE OUTPUT CSV FILES

listing_all_output = OUTPUT_DIR / "combined_listing_all_property_types.csv"
sold_all_output = OUTPUT_DIR / "combined_sold_all_property_types.csv"

listing_res_output = OUTPUT_DIR / "combined_listing_residential.csv"
sold_res_output = OUTPUT_DIR / "combined_sold_residential.csv"

listing_log_output = OUTPUT_DIR / "week1_listing_file_row_counts.csv"
sold_log_output = OUTPUT_DIR / "week1_sold_file_row_counts.csv"

listing_property_counts_output = OUTPUT_DIR / "week1_listing_property_type_counts.csv"
sold_property_counts_output = OUTPUT_DIR / "week1_sold_property_type_counts.csv"

filter_summary_output = OUTPUT_DIR / "week1_residential_filter_summary.csv"


listing_all.to_csv(listing_all_output, index=False)
sold_all.to_csv(sold_all_output, index=False)

listing_residential.to_csv(listing_res_output, index=False)
sold_residential.to_csv(sold_res_output, index=False)

listing_log.to_csv(listing_log_output, index=False)
sold_log.to_csv(sold_log_output, index=False)

listing_property_counts.to_csv(listing_property_counts_output, index=False)
sold_property_counts.to_csv(sold_property_counts_output, index=False)

filter_summary.to_csv(filter_summary_output, index=False)


# 11. FINAL OUTPUT CONFIRMATION

print("WEEK 1 OUTPUT FILES CREATED")
print("-" * 60)

print(f"Saved: {listing_all_output}")
print(f"Saved: {sold_all_output}")
print(f"Saved: {listing_res_output}")
print(f"Saved: {sold_res_output}")
print(f"Saved: {listing_log_output}")
print(f"Saved: {sold_log_output}")
print(f"Saved: {listing_property_counts_output}")
print(f"Saved: {sold_property_counts_output}")
print(f"Saved: {filter_summary_output}")
print()

print("WEEK 1 FINAL SUMMARY")
print("-" * 60)
print(filter_summary)
print()

print("Week 1 aggregation complete.")