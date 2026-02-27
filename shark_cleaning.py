# shark_cleaning.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import re
import pandas as pd


# Config
# -----------------------------
#Month abbreviations and regex patterns for parsing date values.

MONTHS_ABBR = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
MONTH_REGEX = r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"

#dataclass (CleaningConfig) to centralize column names and derived fields,

@dataclass
class CleaningConfig:
    # Column names
    col_date: str = "Date"
    col_time: str = "Time"
    col_country: str = "Country"
    col_fatal: str = "Fatal Y/N"
    col_case_a: str = "Case Number"
    col_case_b: str = "Case Number.1"

    # Output / derived columns
    col_date_complete: str = "Date_complete"
    col_full_date: str = "Full_Date"
    col_year: str = "Year_final"
    col_month: str = "Month"
    col_month_name: str = "Month_name"
    col_day: str = "Day"
    col_date_quality: str = "Date_quality"

    col_hour: str = "Hour"
    col_time_category: str = "Time_category"

    col_case_final: str = "Case_Number_final"

    # Behavior
    drop_invalid_dates: bool = True  # If True, remove rows where Full_Date could not be parsed
    impute_day_for_month_year: str = "01"  # used to build DD-mon-YYYY for mon-YYYY
    date_format: str = "%d-%b-%Y"  # expects DD-mon-YYYY (mon is jan/feb/...)


# -----------------------------
# Helpers (text + report-safe)
# -----------------------------

# normalize_text_series():
# Standardizes a pandas text column by converting to string dtype and
# stripping whitespace and converting to lowercase, while preserving missing values.

def normalize_text_series(s: pd.Series, *, lower: bool = True, strip: bool = True) -> pd.Series:
    """
    Normalize text while preserving missing values (use pandas string dtype).
    """
    s2 = s.astype("string")
    if strip:
        s2 = s2.str.strip()
    if lower:
        s2 = s2.str.lower()
    return s2


# counts_to_json_dict():
# Converts a pandas value_counts() result into a JSON-friendly dictionary by
# ensuring string keys, replacing missing values with "Unknown", and casting
# counts to integers.

def counts_to_json_dict(vc: pd.Series, top_n: Optional[int] = None) -> Dict[str, int]:
 
    if top_n is not None:
        vc = vc.head(top_n)

    out: Dict[str, int] = {}
    for k, v in vc.items():
        if k is pd.NA or pd.isna(k):
            key = "Unknown"
        else:
            key = str(k)
        out[key] = int(v)
    return out


# -----------------------------
# Cleaning steps
# -----------------------------
# clean_case_numbers():
# Builds a single canonical case number column by preferring "Case Number" (A) and
# falling back to "Case Number.1" (B) when A is missing; logs mismatch/pattern stats,
# and drops the redundant case-number columns (and "original order" if present).

def clean_case_numbers(df: pd.DataFrame, cfg: CleaningConfig) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    report: Dict[str, Any] = {}
    out = df.copy()

    a, b = cfg.col_case_a, cfg.col_case_b
    if a not in out.columns and b not in out.columns:
        report["case_number_status"] = "missing_both"
        return out, report

    # Create final with preference for A, fallback to B
    if a in out.columns:
        out[cfg.col_case_final] = out[a]
    else:
        out[cfg.col_case_final] = pd.NA

    if b in out.columns:
        out[cfg.col_case_final] = out[cfg.col_case_final].where(out[cfg.col_case_final].notna(), out[b])

    # Quick diagnostics if both exist
    if a in out.columns and b in out.columns:
        neq = (out[a] != out[b]).sum()
        report["case_number_mismatches_count"] = int(neq)

        pat = r"^\d{4}\.\d{2}\.\d{2}"
        report["case_a_matches_pattern"] = int(out[a].astype("string").str.match(pat, na=False).sum())
        report["case_b_matches_pattern"] = int(out[b].astype("string").str.match(pat, na=False).sum())

    # Drop redundant columns if present
    drop_cols = [c for c in [a, b, "original order"] if c in out.columns]
    if drop_cols:
        out = out.drop(columns=drop_cols)
    report["case_number_dropped_cols"] = drop_cols

    return out, report

# clean_fatal():
# Normalizes the fatality column to three clean categories ("Fatal", "Non-Fatal", "Unknown")
# by uppercasing/stripping, mapping common variants (YES/NO/Y/N/etc.), coercing anything
# else to "Unknown", and reporting value counts.

def clean_fatal(df: pd.DataFrame, cfg: CleaningConfig):
    report = {}
    out = df.copy()
    col = cfg.col_fatal
    if col not in out.columns:
        report["fatal_status"] = "missing"
        return out, report

    s = out[col].astype("string").str.strip().str.upper()

    # Mapping
    s = s.replace({
        "YES": "Y",
        "NO": "N",
        "Y": "Fatal",
        "N": "Non-Fatal",
        "FATAL": "Fatal",
        "NON-FATAL": "Non-Fatal",
        "NON FATAL": "Non-Fatal",
        "UNKNOWN": "Unknown",
        "UNK": "Unknown",
        "N/A": "Unknown",
        "NA": "Unknown",
        "": "Unknown",
    })

    
    s = s.where(s.isin(["Fatal", "Non-Fatal", "Unknown"]), "Unknown")

    out[col] = s
    report["fatal_value_counts"] = counts_to_json_dict(out[col].value_counts(dropna=False))
    return out, report
    return out, report


# clean_country():
# Cleans country names by stripping and converting to Title Case (with a small fix for "USA"),
# then reports the top country frequencies.

def clean_country(df: pd.DataFrame, cfg: CleaningConfig) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    report: Dict[str, Any] = {}
    out = df.copy()

    col = cfg.col_country
    if col not in out.columns:
        report["country_status"] = "missing"
        return out, report

    s = out[col].astype("string").str.strip()

    # Title case is useful for most names but breaks acronyms (USA -> Usa)
    s = s.str.title()
    s = s.replace({"Usa": "USA"})
    out[col] = s

    report["country_value_counts_top"] = counts_to_json_dict(out[col].value_counts(dropna=False), top_n=20)
    return out, report

# _date_quality_masks():
# Creates boolean masks that classify normalized date strings into quality buckets:
# complete (DD-mon-YYYY), month+year (mon-YYYY), or year-only (YYYY).

def _date_quality_masks(date_s: pd.Series) -> Dict[str, pd.Series]:
    """
    Assumes date_s already normalized: lower/strip and 'reported ' removed.
    """
    mask_complete = date_s.str.match(
        rf"^(0?[1-9]|[12][0-9]|3[01])-{MONTH_REGEX}-\d{{4}}$",
        na=False
    )
    mask_month_year = date_s.str.match(rf"^{MONTH_REGEX}-\d{{4}}$", na=False)
    mask_year_only = date_s.str.match(r"^\d{4}$", na=False)

    return {
        "complete": mask_complete,
        "month_year": mask_month_year,
        "year_only": mask_year_only,
    }

# clean_dates():
# Normalizes the raw date text, strips a leading "reported ", classifies date quality
# (Complete / Month_year / Year_only), imputes a default day for month-year values,
# parses a canonical datetime (Full_Date), optionally drops rows with unparseable dates,
# derives year/month/day components, and returns JSON-safe summary stats in a report.

def clean_dates(df: pd.DataFrame, cfg: CleaningConfig) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    report: Dict[str, Any] = {}
    out = df.copy()

    col = cfg.col_date
    if col not in out.columns:
        report["date_status"] = "missing"
        return out, report

    # Normalize
    date_s = normalize_text_series(out[col], lower=True, strip=True)

    # Remove "reported " prefix (your notebook logic)
    date_s = date_s.str.replace(r"^reported\s+", "", regex=True)

    out[col] = date_s

    # Date quality classification
    out[cfg.col_date_quality] = "Unknown"
    masks = _date_quality_masks(date_s)
    out.loc[masks["complete"], cfg.col_date_quality] = "Complete"
    out.loc[masks["month_year"], cfg.col_date_quality] = "Month_year"
    out.loc[masks["year_only"], cfg.col_date_quality] = "Year_only"

    # Build Date_complete (canonical)
    out[cfg.col_date_complete] = date_s

    # Impute day for month-year: "01-jan-1999"
    if masks["month_year"].any():
        out.loc[masks["month_year"], cfg.col_date_complete] = (
            f"{cfg.impute_day_for_month_year}-" + out.loc[masks["month_year"], col]
        )

    # Parse datetime
    out[cfg.col_full_date] = pd.to_datetime(
        out[cfg.col_date_complete],
        format=cfg.date_format,
        errors="coerce",
    )

    # Drop invalid dates (optional)
    report["rows_before_date_filter"] = int(len(out))
    invalid = int(out[cfg.col_full_date].isna().sum())
    report["invalid_full_date_count"] = invalid

    if cfg.drop_invalid_dates:
        out = out[out[cfg.col_full_date].notna()].copy()
        report["rows_after_date_filter"] = int(len(out))
    else:
        report["rows_after_date_filter"] = int(len(out))

    # Derive components
    out[cfg.col_year] = out[cfg.col_full_date].dt.year
    out[cfg.col_month] = out[cfg.col_full_date].dt.month
    out[cfg.col_month_name] = out[cfg.col_full_date].dt.month_name()
    out[cfg.col_day] = out[cfg.col_full_date].dt.day

    # Report counts (JSON safe)
    report["date_quality_counts"] = counts_to_json_dict(out[cfg.col_date_quality].value_counts(dropna=False))
    report["month_name_counts"] = counts_to_json_dict(out[cfg.col_month_name].value_counts(dropna=False))

    return out, report

# extract_hour_from_time():
# Pulls the hour component from time strings formatted like "18h00", "7h", "07h30";
# returns None when no "xh" pattern is found or parsing fails.

def extract_hour_from_time(value: Any) -> Optional[int]:
    """
    Extract hour from strings like '18h00', '7h', '07h30'.
    Returns None if not found.
    """
    if value is None or value is pd.NA:
        return None
    s = str(value).strip().lower()
    m = re.search(r"(\d{1,2})h", s)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            return None
    return None

# classify_hour():
# Buckets an extracted hour into daypart categories (Early morning/Morning/Afternoon/
# Evening/Night), defaulting to "Unknown" for missing/out-of-range values.

def classify_hour(hour):

    if hour is None:
        return "Unknown"

    if 5 <= hour <= 7:
        return "Early morning"

    elif 8 <= hour <= 11:
        return "Morning"

    elif 12 <= hour <= 16:
        return "Afternoon"

    elif 17 <= hour <= 19:
        return "Evening"

    elif 20 <= hour <= 23 or 0 <= hour <= 4:
        return "Night"

    else:
        return "Unknown"

# clean_time():
# Normalizes the time text, extracts an hour (when possible), assigns a time-of-day
# category, overrides categories using keywords (e.g., "morning"), fills missing as
# "Unknown", and reports category counts plus the number of unique raw time values.

def clean_time(df: pd.DataFrame, cfg: CleaningConfig) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    report: Dict[str, Any] = {}
    out = df.copy()

    col = cfg.col_time
    if col not in out.columns:
        report["time_status"] = "missing"
        return out, report

    time_s = normalize_text_series(out[col], lower=True, strip=True)
    out[col] = time_s

    # Extract hour from 'xh'
    out[cfg.col_hour] = out[col].apply(extract_hour_from_time)

    # Bucket into categories
    out[cfg.col_time_category] = out[cfg.col_hour].apply(classify_hour)

    # Keyword overrides (your notebook logic)
    out.loc[out[col].str.contains("early", na=False), cfg.col_time_category] = "Early morning"
    out.loc[out[col].str.contains("morning", na=False), cfg.col_time_category] = "Morning"
    out.loc[out[col].str.contains("afternoon", na=False), cfg.col_time_category] = "Afternoon"
    out.loc[out[col].str.contains("evening", na=False), cfg.col_time_category] = "Evening"
    out.loc[out[col].str.contains("night", na=False), cfg.col_time_category] = "Night"

    # Missing -> Unknown
    out[cfg.col_time_category] = out[cfg.col_time_category].fillna("Unknown")

    report["time_category_counts"] = counts_to_json_dict(out[cfg.col_time_category].value_counts(dropna=False))
    report["unique_time_values"] = int(out[col].nunique(dropna=False))

    return out, report


# build_attack_cube():
# Creates a robust “cube” (multi-dimensional frequency table) by filling missing group
# values with a placeholder, grouping by the requested columns, counting rows via
# size(), and returning integrity checks (sum of counts equals input rows).

def build_attack_cube(
    df: pd.DataFrame,
    group_cols: List[str],
    *,
    fillna_value: str = "Unknown",
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Robust pivot/cube: groupby().size() counts rows exactly.
    """
    report: Dict[str, Any] = {}

    missing = [c for c in group_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns for cube: {missing}")

    df_pivot = df[group_cols].copy()
    df_pivot[group_cols] = df_pivot[group_cols].fillna(fillna_value)

    cube = (
        df_pivot
        .groupby(group_cols, dropna=False)
        .size()
        .reset_index(name="Attack_Count")
    )

    report["cube_rows_in"] = int(len(df_pivot))
    report["cube_attack_count_sum"] = int(cube["Attack_Count"].sum())
    report["cube_integrity_ok"] = bool(report["cube_attack_count_sum"] == report["cube_rows_in"])

    return cube, report


# -----------------------------
# Running the pipeline
# -----------------------------
# run_pipeline():
# Full cleaning workflow: initializes config and a report, applies each
# cleaning step in sequence (case numbers, fatality, country, dates, time), records row
# counts before/after, and optionally builds an aggregated “attack cube” (grouped counts)
# over key dimensions (e.g., Country/Month/Time category/Fatal), returning:
# (cleaned_df, cube_or_none, report).

def run_pipeline(
    df: pd.DataFrame,
    cfg: Optional[CleaningConfig] = None,
    *,
    return_cube: bool = True,
) -> Tuple[pd.DataFrame, Optional[pd.DataFrame], Dict[str, Any]]:
    """
    Main entry point:
    returns (df_clean, cube_or_none, report)
    """
    cfg = cfg or CleaningConfig()

    report: Dict[str, Any] = {
        "initial_rows": int(len(df)),
        "drop_invalid_dates": bool(cfg.drop_invalid_dates),
    }

    out = df.copy()

    out, r = clean_case_numbers(out, cfg); report["case_numbers"] = r
    out, r = clean_fatal(out, cfg);        report["fatal"] = r
    out, r = clean_country(out, cfg);      report["country"] = r
    out, r = clean_dates(out, cfg);        report["dates"] = r
    out, r = clean_time(out, cfg);         report["time"] = r

    report["final_rows"] = int(len(out))

    cube = None
    if return_cube:
        # These are the group columns you were using in the notebook/pivot
        group_cols = [
            cfg.col_country,
            "State",
            "Location",
            cfg.col_month_name,
            cfg.col_time_category,
            cfg.col_fatal,
        ]
        # Only include cols that exist (State/Location may be missing in some datasets)
        group_cols = [c for c in group_cols if c in out.columns]

        cube, r = build_attack_cube(out, group_cols=group_cols)
        report["cube"] = r

    return out, cube, report