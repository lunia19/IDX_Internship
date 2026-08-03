"""
IDX Exchange Data Analyst Internship

Weeks 4–5:
Data Cleaning and Preparation

This script:

1. Loads the Residential and mortgage-enriched datasets created
   during Weeks 2–3.
2. Removes unnecessary or redundant columns where present.
3. Converts important date fields to datetime.
4. Converts important numeric fields to numeric datatypes.
5. Standardises selected text fields.
6. Flags invalid numeric values.
7. Creates date-consistency flags.
8. Creates geographic-quality flags.
9. Removes records containing invalid core numeric values from the
   final analysis-ready datasets.
10. Preserves flagged records in separate CSV files.
11. Produces cleaning, datatype, date-quality, missing-value and
   geographic-quality summaries.
12. Saves cleaned analysis-ready listings and sold datasets.

Important:
Outliers are not removed here. Formal statistical outlier handling
is completed in Week 7 using the IQR method.
"""

# ============================================================
# 1. IMPORT LIBRARIES
# ============================================================

from pathlib import Path

import pandas as pd


# ============================================================
# 2. PROJECT PATHS
# ============================================================

BASE_DIR = Path("/Users/palaklunia/Desktop/IDX_Internship")

INPUT_DIR = BASE_DIR / "outputs" / "weeks2_3"
OUTPUT_DIR = BASE_DIR / "outputs" / "weeks4_5"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


LISTINGS_INPUT_FILE = (
    INPUT_DIR
    / "weeks2_3_listing_residential_enriched.csv"
)

SOLD_INPUT_FILE = (
    INPUT_DIR
    / "weeks2_3_sold_residential_enriched.csv"
)


LISTINGS_OUTPUT_FILE = (
    OUTPUT_DIR
    / "weeks4_5_cleaned_listings.csv"
)

SOLD_OUTPUT_FILE = (
    OUTPUT_DIR
    / "weeks4_5_cleaned_sold.csv"
)


# ============================================================
# 3. CONFIGURATION
# ============================================================

DATE_COLUMNS = [
    "CloseDate",
    "PurchaseContractDate",
    "ListingContractDate",
    "ContractStatusChangeDate"
]


NUMERIC_COLUMNS = [
    "ClosePrice",
    "ListPrice",
    "OriginalListPrice",
    "LivingArea",
    "LotSizeAcres",
    "BedroomsTotal",
    "BathroomsTotalInteger",
    "DaysOnMarket",
    "YearBuilt",
    "Latitude",
    "Longitude",
    "rate_30yr_fixed"
]


TEXT_COLUMNS = [
    "PropertyType",
    "PropertySubType",
    "CountyOrParish",
    "City",
    "StateOrProvince",
    "PostalCode",
    "MLSAreaMajor",
    "ListOfficeName",
    "BuyerOfficeName"
]


# These columns are removed only when they exist.
#
# year_month is retained because it may be useful for validation
# and the next stages of the internship.
#
# Add other clearly unnecessary columns here only after reviewing
# their meaning in the Trestle metadata document.
REDUNDANT_COLUMNS = [
    "Unnamed: 0",
    "index",
    "level_0"
]


# Approximate California coordinate envelope.
#
# These limits are used only to flag implausible coordinates.
# They do not represent a precise California state boundary.
CALIFORNIA_MIN_LATITUDE = 32.0
CALIFORNIA_MAX_LATITUDE = 42.5
CALIFORNIA_MIN_LONGITUDE = -125.0
CALIFORNIA_MAX_LONGITUDE = -114.0


# ============================================================
# 4. HELPER FUNCTIONS
# ============================================================

def print_heading(title):
    """Print a consistent console heading."""

    print()
    print("=" * 75)
    print(title)
    print("=" * 75)


def load_dataset(file_path, dataset_name):
    """
    Load a CSV dataset and confirm that it exists.

    Parameters
    ----------
    file_path : Path
        Location of the CSV file.
    dataset_name : str
        Name used in console messages.

    Returns
    -------
    pandas.DataFrame
        Loaded dataset.
    """

    if not file_path.exists():
        raise FileNotFoundError(
            f"{dataset_name} input file was not found:\n"
            f"{file_path}"
        )

    dataframe = pd.read_csv(
        file_path,
        low_memory=False
    )

    print(
        f"{dataset_name}: "
        f"{len(dataframe):,} rows and "
        f"{len(dataframe.columns):,} columns loaded."
    )

    return dataframe


def remove_redundant_columns(dataframe, dataset_name):
    """
    Remove known unnecessary index-like columns.

    Only columns that actually exist are removed.
    """

    dataframe = dataframe.copy()

    columns_found = [
        column
        for column in REDUNDANT_COLUMNS
        if column in dataframe.columns
    ]

    if columns_found:
        dataframe = dataframe.drop(
            columns=columns_found
        )

        print(
            f"{dataset_name}: removed redundant columns: "
            f"{columns_found}"
        )

    else:
        print(
            f"{dataset_name}: no configured redundant "
            f"columns were found."
        )

    return dataframe, columns_found


def convert_date_columns(dataframe):
    """
    Convert the required MLS date fields to datetime.

    Invalid date strings are converted to NaT so that they can
    be identified through missing-value and date-quality checks.
    """

    dataframe = dataframe.copy()

    for column in DATE_COLUMNS:

        if column in dataframe.columns:

            dataframe[column] = pd.to_datetime(
                dataframe[column],
                errors="coerce"
            )

    return dataframe


def convert_numeric_columns(dataframe):
    """
    Convert configured fields to numeric values.

    Non-numeric entries are converted to NaN.
    """

    dataframe = dataframe.copy()

    for column in NUMERIC_COLUMNS:

        if column in dataframe.columns:

            dataframe[column] = pd.to_numeric(
                dataframe[column],
                errors="coerce"
            )

    return dataframe


def clean_text_columns(dataframe):
    """
    Standardise selected text fields.

    Leading and trailing whitespace is removed.
    Blank text values are converted to missing values.
    """

    dataframe = dataframe.copy()

    for column in TEXT_COLUMNS:

        if column in dataframe.columns:

            dataframe[column] = (
                dataframe[column]
                .astype("string")
                .str.strip()
            )

            dataframe[column] = dataframe[column].replace(
                {
                    "": pd.NA,
                    "nan": pd.NA,
                    "None": pd.NA,
                    "<NA>": pd.NA
                }
            )

    return dataframe


def create_invalid_numeric_flags(dataframe, dataset_name):
    """
    Create boolean flags for invalid numeric values.

    Handbook rules:
    - ClosePrice <= 0
    - LivingArea <= 0
    - DaysOnMarket < 0
    - BedroomsTotal < 0
    - BathroomsTotalInteger < 0

    Missing values are not automatically treated as invalid values.
    They remain available for separate missing-value analysis.
    """

    dataframe = dataframe.copy()

    numeric_rules = {
        "invalid_close_price_flag": (
            "ClosePrice",
            lambda series: series <= 0
        ),
        "invalid_living_area_flag": (
            "LivingArea",
            lambda series: series <= 0
        ),
        "invalid_days_on_market_flag": (
            "DaysOnMarket",
            lambda series: series < 0
        ),
        "invalid_bedrooms_flag": (
            "BedroomsTotal",
            lambda series: series < 0
        ),
        "invalid_bathrooms_flag": (
            "BathroomsTotalInteger",
            lambda series: series < 0
        )
    }

    summary_records = []

    for flag_name, rule_information in numeric_rules.items():

        column_name, rule_function = rule_information

        if column_name in dataframe.columns:

            dataframe[flag_name] = (
                rule_function(dataframe[column_name])
                .fillna(False)
                .astype(bool)
            )

        else:
            dataframe[flag_name] = False

        summary_records.append(
            {
                "dataset": dataset_name,
                "validation_check": flag_name,
                "source_column": column_name,
                "flagged_rows": int(
                    dataframe[flag_name].sum()
                ),
                "flagged_percentage": round(
                    dataframe[flag_name].mean() * 100,
                    4
                )
            }
        )

    invalid_flag_columns = list(
        numeric_rules.keys()
    )

    dataframe["any_invalid_numeric_flag"] = (
        dataframe[invalid_flag_columns]
        .any(axis=1)
    )

    summary_records.append(
        {
            "dataset": dataset_name,
            "validation_check":
                "any_invalid_numeric_flag",
            "source_column":
                "Multiple numeric fields",
            "flagged_rows": int(
                dataframe[
                    "any_invalid_numeric_flag"
                ].sum()
            ),
            "flagged_percentage": round(
                dataframe[
                    "any_invalid_numeric_flag"
                ].mean() * 100,
                4
            )
        }
    )

    summary = pd.DataFrame(
        summary_records
    )

    return dataframe, summary


def create_date_consistency_flags(
    dataframe,
    dataset_name
):
    """
    Create logical date-order validation flags.

    Expected order:
    ListingContractDate
        <= PurchaseContractDate
        <= CloseDate

    Flags:
    - listing_after_close_flag
    - purchase_after_close_flag
    - negative_timeline_flag

    The negative timeline flag is True when any available date
    sequence violates the expected chronological order.
    """

    dataframe = dataframe.copy()

    required_date_columns = {
        "ListingContractDate",
        "PurchaseContractDate",
        "CloseDate"
    }

    available_columns = set(
        dataframe.columns
    )

    if {
        "ListingContractDate",
        "CloseDate"
    }.issubset(available_columns):

        dataframe[
            "listing_after_close_flag"
        ] = (
            dataframe["ListingContractDate"]
            >
            dataframe["CloseDate"]
        ).fillna(False)

    else:
        dataframe[
            "listing_after_close_flag"
        ] = False

    if {
        "PurchaseContractDate",
        "CloseDate"
    }.issubset(available_columns):

        dataframe[
            "purchase_after_close_flag"
        ] = (
            dataframe["PurchaseContractDate"]
            >
            dataframe["CloseDate"]
        ).fillna(False)

    else:
        dataframe[
            "purchase_after_close_flag"
        ] = False

    if required_date_columns.issubset(
        available_columns
    ):

        listing_after_purchase = (
            dataframe["ListingContractDate"]
            >
            dataframe["PurchaseContractDate"]
        ).fillna(False)

        purchase_after_close = (
            dataframe["PurchaseContractDate"]
            >
            dataframe["CloseDate"]
        ).fillna(False)

        listing_after_close = (
            dataframe["ListingContractDate"]
            >
            dataframe["CloseDate"]
        ).fillna(False)

        dataframe[
            "negative_timeline_flag"
        ] = (
            listing_after_purchase
            |
            purchase_after_close
            |
            listing_after_close
        )

    else:

        dataframe[
            "negative_timeline_flag"
        ] = (
            dataframe[
                "listing_after_close_flag"
            ]
            |
            dataframe[
                "purchase_after_close_flag"
            ]
        )

    date_flag_columns = [
        "listing_after_close_flag",
        "purchase_after_close_flag",
        "negative_timeline_flag"
    ]

    dataframe["any_date_issue_flag"] = (
        dataframe[date_flag_columns]
        .any(axis=1)
    )

    summary_records = []

    for flag_name in (
        date_flag_columns
        + ["any_date_issue_flag"]
    ):

        summary_records.append(
            {
                "dataset": dataset_name,
                "date_check": flag_name,
                "flagged_rows": int(
                    dataframe[flag_name].sum()
                ),
                "flagged_percentage": round(
                    dataframe[flag_name].mean()
                    * 100,
                    4
                )
            }
        )

    summary = pd.DataFrame(
        summary_records
    )

    return dataframe, summary


def create_geographic_flags(
    dataframe,
    dataset_name
):
    """
    Create geographic data-quality flags.

    Checks:
    - Missing Latitude or Longitude
    - Latitude or Longitude equals zero
    - Positive Longitude
    - Coordinates outside a broad California plausibility envelope
    """

    dataframe = dataframe.copy()

    if "Latitude" not in dataframe.columns:
        dataframe["Latitude"] = pd.NA

    if "Longitude" not in dataframe.columns:
        dataframe["Longitude"] = pd.NA

    latitude = pd.to_numeric(
        dataframe["Latitude"],
        errors="coerce"
    )

    longitude = pd.to_numeric(
        dataframe["Longitude"],
        errors="coerce"
    )

    dataframe["Latitude"] = latitude
    dataframe["Longitude"] = longitude

    dataframe[
        "missing_coordinates_flag"
    ] = (
        latitude.isna()
        |
        longitude.isna()
    )

    dataframe[
        "zero_coordinates_flag"
    ] = (
        latitude.eq(0)
        |
        longitude.eq(0)
    ).fillna(False)

    dataframe[
        "positive_longitude_flag"
    ] = longitude.gt(0).fillna(False)

    complete_coordinates = (
        latitude.notna()
        &
        longitude.notna()
    )

    outside_latitude_range = (
        latitude.lt(
            CALIFORNIA_MIN_LATITUDE
        )
        |
        latitude.gt(
            CALIFORNIA_MAX_LATITUDE
        )
    )

    outside_longitude_range = (
        longitude.lt(
            CALIFORNIA_MIN_LONGITUDE
        )
        |
        longitude.gt(
            CALIFORNIA_MAX_LONGITUDE
        )
    )

    dataframe[
        "implausible_california_coordinates_flag"
    ] = (
        complete_coordinates
        &
        (
            outside_latitude_range
            |
            outside_longitude_range
        )
    ).fillna(False)

    geographic_flag_columns = [
        "missing_coordinates_flag",
        "zero_coordinates_flag",
        "positive_longitude_flag",
        "implausible_california_coordinates_flag"
    ]

    dataframe[
        "any_geographic_issue_flag"
    ] = (
        dataframe[geographic_flag_columns]
        .any(axis=1)
    )

    summary_records = []

    for flag_name in (
        geographic_flag_columns
        + ["any_geographic_issue_flag"]
    ):

        summary_records.append(
            {
                "dataset": dataset_name,
                "geographic_check": flag_name,
                "flagged_rows": int(
                    dataframe[flag_name].sum()
                ),
                "flagged_percentage": round(
                    dataframe[flag_name].mean()
                    * 100,
                    4
                )
            }
        )

    valid_coordinate_count = int(
        (
            ~dataframe[
                "any_geographic_issue_flag"
            ]
        ).sum()
    )

    summary_records.append(
        {
            "dataset": dataset_name,
            "geographic_check":
                "valid_coordinate_records",
            "flagged_rows":
                valid_coordinate_count,
            "flagged_percentage": round(
                valid_coordinate_count
                / len(dataframe)
                * 100,
                4
            )
            if len(dataframe) > 0
            else 0
        }
    )

    summary = pd.DataFrame(
        summary_records
    )

    return dataframe, summary


def create_missing_value_summary(
    dataframe,
    dataset_name
):
    """Create a missing-value summary for every column."""

    summary = pd.DataFrame(
        {
            "dataset": dataset_name,
            "column_name": dataframe.columns,
            "missing_count":
                dataframe.isna().sum().values
        }
    )

    summary["total_rows"] = len(
        dataframe
    )

    summary["missing_percentage"] = (
        summary["missing_count"]
        / summary["total_rows"]
        * 100
    ).round(4)

    summary = summary.sort_values(
        by="missing_percentage",
        ascending=False
    )

    return summary


def create_dtype_summary(
    dataframe,
    dataset_name
):
    """Create datatype confirmation output."""

    summary = pd.DataFrame(
        {
            "dataset": dataset_name,
            "column_name": dataframe.columns,
            "data_type": (
                dataframe.dtypes
                .astype(str)
                .values
            ),
            "non_null_count": (
                dataframe.notna()
                .sum()
                .values
            ),
            "missing_count": (
                dataframe.isna()
                .sum()
                .values
            )
        }
    )

    return summary


def clean_dataset(
    dataframe,
    dataset_name
):
    """
    Run the complete Weeks 4–5 cleaning process.

    Returns
    -------
    dictionary
        Contains full flagged data, clean data, removed records,
        and all validation summaries.
    """

    original_rows = len(dataframe)
    original_columns = len(
        dataframe.columns
    )

    dataframe, removed_columns = (
        remove_redundant_columns(
            dataframe,
            dataset_name
        )
    )

    dataframe = convert_date_columns(
        dataframe
    )

    dataframe = convert_numeric_columns(
        dataframe
    )

    dataframe = clean_text_columns(
        dataframe
    )

    dataframe, numeric_summary = (
        create_invalid_numeric_flags(
            dataframe,
            dataset_name
        )
    )

    dataframe, date_summary = (
        create_date_consistency_flags(
            dataframe,
            dataset_name
        )
    )

    dataframe, geographic_summary = (
        create_geographic_flags(
            dataframe,
            dataset_name
        )
    )

    missing_summary_before = (
        create_missing_value_summary(
            dataframe,
            f"{dataset_name}_flagged"
        )
    )

    dtype_summary_before = (
        create_dtype_summary(
            dataframe,
            f"{dataset_name}_flagged"
        )
    )

    # Records containing impossible core numeric values are
    # preserved separately and excluded from the cleaned dataset.
    removed_invalid_records = (
        dataframe[
            dataframe[
                "any_invalid_numeric_flag"
            ]
        ]
        .copy()
    )

    cleaned_dataframe = (
        dataframe[
            ~dataframe[
                "any_invalid_numeric_flag"
            ]
        ]
        .copy()
    )

    final_rows = len(
        cleaned_dataframe
    )

    final_columns = len(
        cleaned_dataframe.columns
    )

    missing_summary_after = (
        create_missing_value_summary(
            cleaned_dataframe,
            f"{dataset_name}_cleaned"
        )
    )

    dtype_summary_after = (
        create_dtype_summary(
            cleaned_dataframe,
            f"{dataset_name}_cleaned"
        )
    )

    row_summary = pd.DataFrame(
        [
            {
                "dataset": dataset_name,
                "original_rows": original_rows,
                "cleaned_rows": final_rows,
                "removed_invalid_rows":
                    original_rows - final_rows,
                "rows_retained_percentage":
                    round(
                        final_rows
                        / original_rows
                        * 100,
                        4
                    )
                    if original_rows > 0
                    else 0,
                "original_columns":
                    original_columns,
                "final_columns":
                    final_columns,
                "redundant_columns_removed":
                    len(removed_columns),
                "removed_column_names":
                    ", ".join(
                        removed_columns
                    )
            }
        ]
    )

    return {
        "flagged_data": dataframe,
        "cleaned_data":
            cleaned_dataframe,
        "removed_invalid_records":
            removed_invalid_records,
        "numeric_summary":
            numeric_summary,
        "date_summary":
            date_summary,
        "geographic_summary":
            geographic_summary,
        "missing_summary_before":
            missing_summary_before,
        "missing_summary_after":
            missing_summary_after,
        "dtype_summary_before":
            dtype_summary_before,
        "dtype_summary_after":
            dtype_summary_after,
        "row_summary":
            row_summary
    }


# ============================================================
# 5. LOAD WEEKS 2–3 OUTPUTS
# ============================================================

print_heading(
    "WEEKS 4–5: DATA CLEANING AND PREPARATION"
)

print("Loading Weeks 2–3 enriched datasets...")

listings_raw = load_dataset(
    LISTINGS_INPUT_FILE,
    "Listings"
)

sold_raw = load_dataset(
    SOLD_INPUT_FILE,
    "Sold"
)


# ============================================================
# 6. CLEAN LISTINGS DATASET
# ============================================================

print_heading(
    "CLEANING LISTINGS DATASET"
)

listings_results = clean_dataset(
    listings_raw,
    "listings"
)


# ============================================================
# 7. CLEAN SOLD DATASET
# ============================================================

print_heading(
    "CLEANING SOLD DATASET"
)

sold_results = clean_dataset(
    sold_raw,
    "sold"
)


# ============================================================
# 8. COMBINE SUMMARY REPORTS
# ============================================================

row_count_summary = pd.concat(
    [
        listings_results[
            "row_summary"
        ],
        sold_results[
            "row_summary"
        ]
    ],
    ignore_index=True
)


numeric_validation_summary = pd.concat(
    [
        listings_results[
            "numeric_summary"
        ],
        sold_results[
            "numeric_summary"
        ]
    ],
    ignore_index=True
)


date_consistency_summary = pd.concat(
    [
        listings_results[
            "date_summary"
        ],
        sold_results[
            "date_summary"
        ]
    ],
    ignore_index=True
)


geographic_quality_summary = pd.concat(
    [
        listings_results[
            "geographic_summary"
        ],
        sold_results[
            "geographic_summary"
        ]
    ],
    ignore_index=True
)


missing_values_before = pd.concat(
    [
        listings_results[
            "missing_summary_before"
        ],
        sold_results[
            "missing_summary_before"
        ]
    ],
    ignore_index=True
)


missing_values_after = pd.concat(
    [
        listings_results[
            "missing_summary_after"
        ],
        sold_results[
            "missing_summary_after"
        ]
    ],
    ignore_index=True
)


dtype_confirmation_before = pd.concat(
    [
        listings_results[
            "dtype_summary_before"
        ],
        sold_results[
            "dtype_summary_before"
        ]
    ],
    ignore_index=True
)


dtype_confirmation_after = pd.concat(
    [
        listings_results[
            "dtype_summary_after"
        ],
        sold_results[
            "dtype_summary_after"
        ]
    ],
    ignore_index=True
)


# ============================================================
# 9. CREATE TRANSFORMATION LOG
# ============================================================

transformation_log = pd.DataFrame(
    [
        {
            "step_number": 1,
            "transformation":
                "Loaded enriched Residential datasets",
            "reason":
                "Use the validated and mortgage-enriched "
                "Weeks 2–3 outputs as inputs."
        },
        {
            "step_number": 2,
            "transformation":
                "Removed unnecessary index-like columns",
            "reason":
                "Prevent redundant fields from entering "
                "the analysis-ready datasets."
        },
        {
            "step_number": 3,
            "transformation":
                "Converted MLS date fields to datetime",
            "reason":
                "Enable chronological validation and "
                "future time-series calculations."
        },
        {
            "step_number": 4,
            "transformation":
                "Converted analysis fields to numeric",
            "reason":
                "Ensure arithmetic, summaries and "
                "validation rules work correctly."
        },
        {
            "step_number": 5,
            "transformation":
                "Standardised selected text fields",
            "reason":
                "Remove leading and trailing whitespace "
                "and convert blank strings to null."
        },
        {
            "step_number": 6,
            "transformation":
                "Created invalid numeric flags",
            "reason":
                "Identify impossible values such as "
                "non-positive prices or living area."
        },
        {
            "step_number": 7,
            "transformation":
                "Created date consistency flags",
            "reason":
                "Identify records that violate expected "
                "listing, contract and closing order."
        },
        {
            "step_number": 8,
            "transformation":
                "Created geographic quality flags",
            "reason":
                "Identify missing, zero, positive or "
                "implausible California coordinates."
        },
        {
            "step_number": 9,
            "transformation":
                "Excluded invalid core numeric records",
            "reason":
                "Create analysis-ready datasets while "
                "preserving removed records separately."
        },
        {
            "step_number": 10,
            "transformation":
                "Retained date and geographic issue flags",
            "reason":
                "Keep quality information available for "
                "later analysis instead of deleting all "
                "flagged records."
        }
    ]
)


# ============================================================
# 10. SAVE CLEANED DATASETS
# ============================================================

print_heading(
    "SAVING CLEANED DATASETS"
)

listings_results[
    "cleaned_data"
].to_csv(
    LISTINGS_OUTPUT_FILE,
    index=False
)


sold_results[
    "cleaned_data"
].to_csv(
    SOLD_OUTPUT_FILE,
    index=False
)


print(
    f"Cleaned listings saved to:\n"
    f"{LISTINGS_OUTPUT_FILE}"
)

print()

print(
    f"Cleaned sold data saved to:\n"
    f"{SOLD_OUTPUT_FILE}"
)


# ============================================================
# 11. SAVE FULL FLAGGED DATASETS
# ============================================================

listings_results[
    "flagged_data"
].to_csv(
    OUTPUT_DIR
    / "weeks4_5_flagged_listings.csv",
    index=False
)


sold_results[
    "flagged_data"
].to_csv(
    OUTPUT_DIR
    / "weeks4_5_flagged_sold.csv",
    index=False
)


# ============================================================
# 12. SAVE REMOVED INVALID RECORDS
# ============================================================

listings_results[
    "removed_invalid_records"
].to_csv(
    OUTPUT_DIR
    / "weeks4_5_removed_invalid_listings.csv",
    index=False
)


sold_results[
    "removed_invalid_records"
].to_csv(
    OUTPUT_DIR
    / "weeks4_5_removed_invalid_sold.csv",
    index=False
)


# ============================================================
# 13. SAVE SUMMARY REPORTS
# ============================================================

row_count_summary.to_csv(
    OUTPUT_DIR
    / "weeks4_5_row_count_summary.csv",
    index=False
)


numeric_validation_summary.to_csv(
    OUTPUT_DIR
    / "weeks4_5_numeric_validation_summary.csv",
    index=False
)


date_consistency_summary.to_csv(
    OUTPUT_DIR
    / "weeks4_5_date_consistency_summary.csv",
    index=False
)


geographic_quality_summary.to_csv(
    OUTPUT_DIR
    / "weeks4_5_geographic_quality_summary.csv",
    index=False
)


missing_values_before.to_csv(
    OUTPUT_DIR
    / "weeks4_5_missing_values_before_cleaning.csv",
    index=False
)


missing_values_after.to_csv(
    OUTPUT_DIR
    / "weeks4_5_missing_values_after_cleaning.csv",
    index=False
)


dtype_confirmation_before.to_csv(
    OUTPUT_DIR
    / "weeks4_5_dtype_confirmation_before.csv",
    index=False
)


dtype_confirmation_after.to_csv(
    OUTPUT_DIR
    / "weeks4_5_dtype_confirmation_after.csv",
    index=False
)


transformation_log.to_csv(
    OUTPUT_DIR
    / "weeks4_5_transformation_log.csv",
    index=False
)


# ============================================================
# 14. PRINT VALIDATION RESULTS
# ============================================================

print_heading(
    "ROW COUNT SUMMARY"
)

print(
    row_count_summary.to_string(
        index=False
    )
)


print_heading(
    "INVALID NUMERIC VALUE SUMMARY"
)

print(
    numeric_validation_summary.to_string(
        index=False
    )
)


print_heading(
    "DATE CONSISTENCY SUMMARY"
)

print(
    date_consistency_summary.to_string(
        index=False
    )
)


print_heading(
    "GEOGRAPHIC DATA QUALITY SUMMARY"
)

print(
    geographic_quality_summary.to_string(
        index=False
    )
)


# ============================================================
# 15. CONFIRM IMPORTANT DATA TYPES
# ============================================================

print_heading(
    "IMPORTANT DATA TYPE CONFIRMATION"
)

important_confirmation_columns = (
    DATE_COLUMNS
    + NUMERIC_COLUMNS
)


for dataset_name, dataframe in [
    (
        "Cleaned listings",
        listings_results[
            "cleaned_data"
        ]
    ),
    (
        "Cleaned sold",
        sold_results[
            "cleaned_data"
        ]
    )
]:

    print()
    print(dataset_name)
    print("-" * 75)

    available_columns = [
        column
        for column in important_confirmation_columns
        if column in dataframe.columns
    ]

    print(
        dataframe[
            available_columns
        ]
        .dtypes
        .to_string()
    )


# ============================================================
# 16. FINAL COMPLETION MESSAGE
# ============================================================

print_heading(
    "WEEKS 4–5 COMPLETED SUCCESSFULLY"
)

print(
    f"Cleaned listings rows: "
    f"{len(listings_results['cleaned_data']):,}"
)

print(
    f"Cleaned sold rows: "
    f"{len(sold_results['cleaned_data']):,}"
)

print(
    f"Removed invalid listing rows: "
    f"{len(listings_results['removed_invalid_records']):,}"
)

print(
    f"Removed invalid sold rows: "
    f"{len(sold_results['removed_invalid_records']):,}"
)

print()

print(
    "Date-quality and geographic-quality records were "
    "flagged and retained unless they also contained an "
    "invalid core numeric value."
)

print()

print(
    f"All Weeks 4–5 outputs were saved to:\n"
    f"{OUTPUT_DIR}"
)