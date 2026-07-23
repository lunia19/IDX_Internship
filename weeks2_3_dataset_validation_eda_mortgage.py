# Weeks 2-3:
# Data Structuring, Validation, EDA, and Mortgage Analysis

# Purpose:
    # 1. Load the combined MLS datasets created in Week 1.
    # 2. Inspect dataset structure and data types.
    # 3. Document unique PropertyType values.
    # 4. Filter both datasets to Residential properties.
    # 5. Analyse missing values and flag columns above 90% missing.
    # 6. Create numeric distribution summaries.
    # 7. Answer key exploratory data analysis questions.
    # 8. Enrich listings and sold datasets with monthly 30-year mortgage rates.
    # 9. Validate the mortgage-rate merge.
    # 10. Produce three EDA graphs.
    # 11. Save all outputs for Weeks 4–5.

# Author: Palak Lunia

# 1. IMPORT REQUIRED LIBRARIES

import pandas as pd 
import matplotlib.pyplot as plt
from pathlib import Path

# 2. SET PROJECT PATHS

BASE_DIR = Path("/Users/palaklunia/Desktop/IDX_Internship")

WEEK1_DIR = BASE_DIR / "outputs" / "week1"

OUTPUT_DIR = BASE_DIR / "outputs" / "weeks2_3"
GRAPHS_DIR = OUTPUT_DIR / "graphs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
GRAPHS_DIR.mkdir(parents=True, exist_ok=True)

# Week 1 combined datasets before residential filtering 
LISTING_FILE = WEEK1_DIR / "combined_listing_all_property_types.csv"
SOLD_FILE = WEEK1_DIR / "combined_sold_all_property_types.csv"

# Local mortgage file as backup 
MORTGAGE_LOCAL_FILE = BASE_DIR / "raw_csv" / "MORTGAGE30US.csv"

# 3. LOAD WEAK1 DATASETS

print()
print("=" * 70)
print("WEEKS 2–3: DATASET VALIDATION, EDA AND MORTGAGE ENRICHMENT")
print("=" * 70)
print()

print("Loading Week 1 combined datasets...")
print("-" * 70)

listings_all = pd.read_csv(
    LISTING_FILE,
    low_memory=False
)

sold_all = pd.read_csv(
    SOLD_FILE,
    low_memory=False
)

print(
    f"Listings dataset: "
    f"{listings_all.shape[0]:,} rows, "
    f"{listings_all.shape[1]} columns"
)

print(
    f"Sold dataset: "
    f"{sold_all.shape[0]:,} rows, "
    f"{sold_all.shape[1]} columns"
)

print()

# 4. DATA STRUCTURE SUMMARY

print("DATASET STRUCTURE SUMMARY")
print("-" * 70)

structure_summary = pd.DataFrame(
    [
        {
            "dataset": "listings_all",
            "rows": listings_all.shape[0],
            "columns": listings_all.shape[1],
            "duplicate_rows": listings_all.duplicated().sum()
        },
        {
            "dataset": "sold_all",
            "rows": sold_all.shape[0],
            "columns": sold_all.shape[1],
            "duplicate_rows": sold_all.duplicated().sum()
        }
    ]
)

print(structure_summary)
print()

structure_summary.to_csv(
    OUTPUT_DIR / "weeks2_3_dataset_structure_summary.csv",
    index=False
)

# 5. DATA TYPE SUMMARY
print("Creating data type summary...")
print()

listing_dtypes = (
    listings_all
    .dtypes
    .astype(str)
    .reset_index()
)

listing_dtypes.columns = [
    "column_name",
    "data_type"
]

listing_dtypes["dataset"] = "listings"


sold_dtypes = (
    sold_all
    .dtypes
    .astype(str)
    .reset_index()
)

sold_dtypes.columns = [
    "column_name",
    "data_type"
]

sold_dtypes["dataset"] = "sold"


dtype_summary = pd.concat(
    [
        listing_dtypes,
        sold_dtypes
    ],
    ignore_index=True
)

dtype_summary.to_csv(
    OUTPUT_DIR / "weeks2_3_dtype_summary.csv",
    index=False
)

# 6. UNIQUE PROPERTY TYPES
print("PROPERTY TYPES FOUND")
print("-" * 70)

listing_property_types = (
    listings_all["PropertyType"]
    .value_counts(dropna=False)
    .reset_index()
)

listing_property_types.columns = [
    "PropertyType",
    "row_count"
]

listing_property_types["percentage"] = (
    listing_property_types["row_count"]
    / len(listings_all)
    * 100
).round(2)


sold_property_types = (
    sold_all["PropertyType"]
    .value_counts(dropna=False)
    .reset_index()
)

sold_property_types.columns = [
    "PropertyType",
    "row_count"
]

sold_property_types["percentage"] = (
    sold_property_types["row_count"]
    / len(sold_all)
    * 100
).round(2)


print("Listings:")
print(listing_property_types)
print()

print("Sold:")
print(sold_property_types)
print()


listing_property_types.to_csv(
    OUTPUT_DIR / "weeks2_3_listing_property_types.csv",
    index=False
)

sold_property_types.to_csv(
    OUTPUT_DIR / "weeks2_3_sold_property_types.csv",
    index=False
)

# 7. FILTER TO RESIDENTIAL 
print("RESIDENTIAL FILTER")
print("-" * 70)

listing_before = len(listings_all)
sold_before = len(sold_all)


listings = listings_all[
    listings_all["PropertyType"] == "Residential"
].copy()

sold = sold_all[
    sold_all["PropertyType"] == "Residential"
].copy()


listing_after = len(listings)
sold_after = len(sold)


filter_summary = pd.DataFrame(
    [
        {
            "dataset": "listings",
            "rows_before_filter": listing_before,
            "rows_after_filter": listing_after,
            "rows_removed": listing_before - listing_after,
            "residential_share_percent": round(
                listing_after / listing_before * 100,
                2
            )
        },
        {
            "dataset": "sold",
            "rows_before_filter": sold_before,
            "rows_after_filter": sold_after,
            "rows_removed": sold_before - sold_after,
            "residential_share_percent": round(
                sold_after / sold_before * 100,
                2
            )
        }
    ]
)


print(filter_summary)
print()

filter_summary.to_csv(
    OUTPUT_DIR / "weeks2_3_residential_filter_summary.csv",
    index=False
)

# 8. MISSING VALUE ANALYSIS

def create_missing_summary(
    df,
    dataset_name
):
    """
    Create a missing-value report for every column.

    Includes:
    - missing count
    - missing percentage
    - flag for columns above 90% missing
    """

    summary = pd.DataFrame(
        {
            "column_name": df.columns,
            "missing_count": df.isna().sum().values,
            "total_rows": len(df)
        }
    )

    summary["missing_percent"] = (
        summary["missing_count"]
        / summary["total_rows"]
        * 100
    ).round(2)

    summary[
        "above_90_percent_missing"
    ] = (
        summary["missing_percent"] > 90
    )

    summary["dataset"] = dataset_name

    summary = summary.sort_values(
        by="missing_percent",
        ascending=False
    )

    return summary


listing_null_summary = create_missing_summary(
    listings,
    "listings"
)

sold_null_summary = create_missing_summary(
    sold,
    "sold"
)


print("TOP 10 MISSING COLUMNS – LISTINGS")
print("-" * 70)
print(listing_null_summary.head(10))
print()

print("TOP 10 MISSING COLUMNS – SOLD")
print("-" * 70)
print(sold_null_summary.head(10))
print()


listing_null_summary.to_csv(
    OUTPUT_DIR / "weeks2_3_listing_missing_values.csv",
    index=False
)

sold_null_summary.to_csv(
    OUTPUT_DIR / "weeks2_3_sold_missing_values.csv",
    index=False
)


# Save only columns above 90% missing
high_missing_columns = pd.concat(
    [
        listing_null_summary[
            listing_null_summary[
                "above_90_percent_missing"
            ]
        ],
        sold_null_summary[
            sold_null_summary[
                "above_90_percent_missing"
            ]
        ]
    ],
    ignore_index=True
)

high_missing_columns.to_csv(
    OUTPUT_DIR / "weeks2_3_columns_above_90_percent_missing.csv",
    index=False
)

# 9. PREPARE NUMERIC FIELDS

numeric_fields = [
    "ClosePrice",
    "ListPrice",
    "OriginalListPrice",
    "LivingArea",
    "LotSizeAcres",
    "BedroomsTotal",
    "BathroomsTotalInteger",
    "DaysOnMarket",
    "YearBuilt"
]


def convert_numeric_columns(
    df,
    columns
):

    for column in columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    return df


listings = convert_numeric_columns(
    listings,
    numeric_fields
)

sold = convert_numeric_columns(
    sold,
    numeric_fields
)

# 10. NUMERIC DISTRIBUTION SUMMARY

def create_numeric_summary(
    df,
    dataset_name,
    fields
):

    available_fields = [
        field
        for field in fields
        if field in df.columns
    ]

    summary = (
        df[available_fields]
        .describe(
            percentiles=[
                0.01,
                0.05,
                0.25,
                0.50,
                0.75,
                0.95,
                0.99
            ]
        )
        .T
        .reset_index()
    )

    summary = summary.rename(
        columns={
            "index": "field",
            "50%": "median"
        }
    )

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


listing_numeric_summary.to_csv(
    OUTPUT_DIR / "weeks2_3_listing_numeric_summary.csv",
    index=False
)

sold_numeric_summary.to_csv(
    OUTPUT_DIR / "weeks2_3_sold_numeric_summary.csv",
    index=False
)


print("SOLD NUMERIC SUMMARY")
print("-" * 70)

important_sold_fields = sold_numeric_summary[
    sold_numeric_summary[
        "field"
    ].isin(
        [
            "ClosePrice",
            "LivingArea",
            "DaysOnMarket"
        ]
    )
]

print(important_sold_fields)
print()

# 11. CONVERT DATE FIELDS

date_columns_listing = [
    "ListingContractDate",
    "PurchaseContractDate",
    "ContractStatusChangeDate",
    "CloseDate"
]

date_columns_sold = [
    "ListingContractDate",
    "PurchaseContractDate",
    "ContractStatusChangeDate",
    "CloseDate"
]


for column in date_columns_listing:

    if column in listings.columns:

        listings[column] = pd.to_datetime(
            listings[column],
            errors="coerce"
        )


for column in date_columns_sold:

    if column in sold.columns:

        sold[column] = pd.to_datetime(
            sold[column],
            errors="coerce"
        )

# 12. CORE EDA QUESTIONS

print("CORE EXPLORATORY DATA ANALYSIS")
print("-" * 70)

    # Average and median close price
average_close_price = (
    sold["ClosePrice"].mean()
)

median_close_price = (
    sold["ClosePrice"].median()
)


print(
    f"Average ClosePrice: "
    f"${average_close_price:,.2f}"
)

print(
    f"Median ClosePrice: "
    f"${median_close_price:,.2f}"
)

print()

    # Days on Market
dom_summary = sold[
    "DaysOnMarket"
].describe()

print("DaysOnMarket summary:")
print(dom_summary)
print()

    # Sold above / below / at list price
valid_price_records = sold[
    (
        sold["ClosePrice"].notna()
    )
    &
    (
        sold["ListPrice"].notna()
    )
    &
    (
        sold["ListPrice"] > 0
    )
].copy()


above_list = (
    valid_price_records[
        "ClosePrice"
    ]
    >
    valid_price_records[
        "ListPrice"
    ]
).sum()


below_list = (
    valid_price_records[
        "ClosePrice"
    ]
    <
    valid_price_records[
        "ListPrice"
    ]
).sum()


at_list = (
    valid_price_records[
        "ClosePrice"
    ]
    ==
    valid_price_records[
        "ListPrice"
    ]
).sum()


total_valid_prices = len(
    valid_price_records
)


price_position_summary = pd.DataFrame(
    [
        {
            "sale_position": "Above List Price",
            "count": above_list,
            "percentage": round(
                above_list
                / total_valid_prices
                * 100,
                2
            )
        },
        {
            "sale_position": "Below List Price",
            "count": below_list,
            "percentage": round(
                below_list
                / total_valid_prices
                * 100,
                2
            )
        },
        {
            "sale_position": "At List Price",
            "count": at_list,
            "percentage": round(
                at_list
                / total_valid_prices
                * 100,
                2
            )
        }
    ]
)


print("Sold relative to ListPrice:")
print(price_position_summary)
print()

price_position_summary.to_csv(
    OUTPUT_DIR / "weeks2_3_sold_vs_list_price_summary.csv",
    index=False
)

    # Date consistency checks
listing_after_close_count = 0
purchase_after_close_count = 0
purchase_before_listing_count = 0


if (
    "ListingContractDate" in sold.columns
    and
    "CloseDate" in sold.columns
):

    listing_after_close_count = (
        sold["ListingContractDate"]
        >
        sold["CloseDate"]
    ).sum()


if (
    "PurchaseContractDate" in sold.columns
    and
    "CloseDate" in sold.columns
):

    purchase_after_close_count = (
        sold["PurchaseContractDate"]
        >
        sold["CloseDate"]
    ).sum()


if (
    "PurchaseContractDate" in sold.columns
    and
    "ListingContractDate" in sold.columns
):

    purchase_before_listing_count = (
        sold["PurchaseContractDate"]
        <
        sold["ListingContractDate"]
    ).sum()


date_issue_summary = pd.DataFrame(
    [
        {
            "issue": "ListingContractDate after CloseDate",
            "count": listing_after_close_count
        },
        {
            "issue": "PurchaseContractDate after CloseDate",
            "count": purchase_after_close_count
        },
        {
            "issue": "PurchaseContractDate before ListingContractDate",
            "count": purchase_before_listing_count
        }
    ]
)


print("Date consistency issues:")
print(date_issue_summary)
print()

date_issue_summary.to_csv(
    OUTPUT_DIR / "weeks2_3_date_consistency_summary.csv",
    index=False
)

    # Counties with highest median prices
county_price_summary = (
    sold[
        [
            "CountyOrParish",
            "ClosePrice"
        ]
    ]
    .dropna()
    .groupby(
        "CountyOrParish"
    )
    .agg(
        median_close_price=(
            "ClosePrice",
            "median"
        ),
        sales_count=(
            "ClosePrice",
            "count"
        )
    )
    .reset_index()
    .sort_values(
        "median_close_price",
        ascending=False
    )
)


print(
    "Top 10 counties by median ClosePrice:"
)

print(
    county_price_summary.head(10)
)

print()


county_price_summary.to_csv(
    OUTPUT_DIR / "weeks2_3_county_median_prices.csv",
    index=False
)

# 13. MORTGAGE RATE DATA

print("MORTGAGE RATE ENRICHMENT")
print("-" * 70)


FRED_URL = (
    "https://fred.stlouisfed.org/"
    "graph/fredgraph.csv?id=MORTGAGE30US"
)


try:

    print(
        "Attempting to download MORTGAGE30US "
        "directly from FRED..."
    )

    mortgage = pd.read_csv(
        FRED_URL
    )

    print(
        "Mortgage data downloaded successfully."
    )


except Exception as error:

    print(
        "Could not download from FRED."
    )

    print(
        "Using local MORTGAGE30US.csv instead."
    )

    print(
        f"Download error: {error}"
    )

    mortgage = pd.read_csv(
        MORTGAGE_LOCAL_FILE
    )


print(
    f"Mortgage observations loaded: "
    f"{len(mortgage):,}"
)

print()

# 14. PREPARE MORTGAGE DATA


mortgage[
    "observation_date"
] = pd.to_datetime(
    mortgage[
        "observation_date"
    ],
    errors="coerce"
)


mortgage[
    "MORTGAGE30US"
] = pd.to_numeric(
    mortgage[
        "MORTGAGE30US"
    ],
    errors="coerce"
)


# Create year-month key
mortgage[
    "year_month"
] = mortgage[
    "observation_date"
].dt.to_period("M")


# Weekly observations → monthly average
mortgage_monthly = (
    mortgage
    .groupby(
        "year_month"
    )[
        "MORTGAGE30US"
    ]
    .mean()
    .reset_index()
)


mortgage_monthly = mortgage_monthly.rename(
    columns={
        "MORTGAGE30US":
        "rate_30yr_fixed"
    }
)


print(
    "Monthly mortgage rate preview:"
)

print(
    mortgage_monthly.head()
)

print()


mortgage_monthly.to_csv(
    OUTPUT_DIR / "weeks2_3_monthly_mortgage_rates.csv",
    index=False
)

# 15. CREATE YEAR-MONTH KEYS ON MLS DATA

listings[
    "year_month"
] = listings[
    "ListingContractDate"
].dt.to_period("M")


sold[
    "year_month"
] = sold[
    "CloseDate"
].dt.to_period("M")

# 16. MERGE MORTGAGE RATES

listing_rows_before_merge = len(
    listings
)

sold_rows_before_merge = len(
    sold
)


listings_enriched = listings.merge(
    mortgage_monthly,
    on="year_month",
    how="left"
)


sold_enriched = sold.merge(
    mortgage_monthly,
    on="year_month",
    how="left"
)


listing_rows_after_merge = len(
    listings_enriched
)

sold_rows_after_merge = len(
    sold_enriched
)

# 17. VALIDATE MORTGAGE MERGE

listing_rate_nulls = (
    listings_enriched[
        "rate_30yr_fixed"
    ]
    .isna()
    .sum()
)

sold_rate_nulls = (
    sold_enriched[
        "rate_30yr_fixed"
    ]
    .isna()
    .sum()
)


merge_validation = pd.DataFrame(
    [
        {
            "dataset": "listings",
            "rows_before_merge":
            listing_rows_before_merge,
            "rows_after_merge":
            listing_rows_after_merge,
            "null_mortgage_rates":
            listing_rate_nulls
        },
        {
            "dataset": "sold",
            "rows_before_merge":
            sold_rows_before_merge,
            "rows_after_merge":
            sold_rows_after_merge,
            "null_mortgage_rates":
            sold_rate_nulls
        }
    ]
)


print("Mortgage merge validation:")
print(merge_validation)
print()


merge_validation.to_csv(
    OUTPUT_DIR / "weeks2_3_mortgage_merge_validation.csv",
    index=False
)


# Preview requested fields
preview_columns = [
    "CloseDate",
    "year_month",
    "ClosePrice",
    "rate_30yr_fixed"
]


print("Sold mortgage-rate merge preview:")

print(
    sold_enriched[
        preview_columns
    ].head()
)

print()

# 18. SAVE FILTERED AND ENRICHED DATASETS

print(
    "Saving Residential enriched datasets..."
)


listings_enriched.to_csv(
    OUTPUT_DIR
    / "weeks2_3_listing_residential_enriched.csv",
    index=False
)


sold_enriched.to_csv(
    OUTPUT_DIR
    / "weeks2_3_sold_residential_enriched.csv",
    index=False
)


print(
    "Datasets saved successfully."
)

print()

# 19. GRAPH 1
    # CLOSEPRICE HISTOGRAM

print("Creating Graph 1...")


graph_close_price = sold_enriched[
    "ClosePrice"
].dropna()


# Limit graph to 1st–99th percentiles
# so extreme outliers do not destroy readability.
close_low = graph_close_price.quantile(
    0.01
)

close_high = graph_close_price.quantile(
    0.99
)


graph_close_price = graph_close_price[
    (
        graph_close_price
        >= close_low
    )
    &
    (
        graph_close_price
        <= close_high
    )
]


plt.figure(
    figsize=(11, 6)
)

plt.hist(
    graph_close_price,
    bins=50
)

plt.title(
    "Distribution of Residential Close Prices"
)

plt.xlabel(
    "Close Price ($)"
)

plt.ylabel(
    "Number of Sales"
)

plt.ticklabel_format(
    style="plain",
    axis="x"
)

plt.tight_layout()


plt.savefig(
    GRAPHS_DIR
    / "graph1_close_price_histogram.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# 20. GRAPH 2
    # LIVINGAREA BOXPLOT

print("Creating Graph 2...")


graph_living_area = sold_enriched[
    "LivingArea"
].dropna()


# Restrict graph to 99th percentile
# for readable visualisation.
living_upper = graph_living_area.quantile(
    0.99
)

graph_living_area = graph_living_area[
    (
        graph_living_area > 0
    )
    &
    (
        graph_living_area
        <= living_upper
    )
]


plt.figure(
    figsize=(10, 5)
)

plt.boxplot(
    graph_living_area,
    vert=False
)

plt.title(
    "Distribution of Residential Living Area"
)

plt.xlabel(
    "Living Area (Square Feet)"
)

plt.tight_layout()


plt.savefig(
    GRAPHS_DIR
    / "graph2_living_area_boxplot.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# 21. GRAPH 3
    # DAYSONMARKET HISTOGRAM

print("Creating Graph 3...")


graph_dom = sold_enriched[
    "DaysOnMarket"
].dropna()


dom_upper = graph_dom.quantile(
    0.99
)


graph_dom = graph_dom[
    (
        graph_dom >= 0
    )
    &
    (
        graph_dom
        <= dom_upper
    )
]


plt.figure(
    figsize=(11, 6)
)

plt.hist(
    graph_dom,
    bins=50
)

plt.title(
    "Distribution of Residential Days on Market"
)

plt.xlabel(
    "Days on Market"
)

plt.ylabel(
    "Number of Sales"
)

plt.tight_layout()


plt.savefig(
    GRAPHS_DIR
    / "graph3_days_on_market_histogram.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


print(
    "All three graphs created successfully."
)

print()

# 22. FINAL SUMMARY

print("=" * 70)

print(
    "WEEKS 2–3 COMPLETED SUCCESSFULLY"
)

print("=" * 70)

print()

print(
    f"Residential listing rows: "
    f"{len(listings_enriched):,}"
)

print(
    f"Residential sold rows: "
    f"{len(sold_enriched):,}"
)

print(
    f"Listing mortgage-rate nulls: "
    f"{listing_rate_nulls:,}"
)

print(
    f"Sold mortgage-rate nulls: "
    f"{sold_rate_nulls:,}"
)

print()

print(
    f"Outputs saved to:"
)

print(
    OUTPUT_DIR
)

print()

print(
    f"Graphs saved to:"
)

print(
    GRAPHS_DIR
)

print()

print(
    "Weeks 2–3 dataset validation, EDA, "
    "and mortgage enrichment complete."
)