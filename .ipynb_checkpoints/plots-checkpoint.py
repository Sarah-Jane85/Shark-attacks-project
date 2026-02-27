# Expected columns (from shark_cleaning.py output):
#   Year_final, Month, Month_name, Time_category, Country, Fatal Y/N

from __future__ import annotations

from pathlib import Path
from typing import Optional, Sequence

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# Calendar order for months (used to keep plots correctly sorted)
MONTH_ORDER = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

# Logical order for time-of-day categories
TIME_CATEGORY_ORDER = ["Early morning", "Morning", "Afternoon", "Evening", "Night", "Unknown"]


def _ensure_outdir(out_dir: Optional[str | Path]) -> Optional[Path]:
    """
    Ensure that the output directory exists.
    If None is provided, no directory is created.
    """
    if out_dir is None:
        return None

    out_path = Path(out_dir)

    # Create directory if it does not exist
    out_path.mkdir(parents=True, exist_ok=True)

    return out_path


def _finalize(fig: plt.Figure, outpath: Optional[Path], show: bool = False, dpi: int = 150) -> None:
    """
    Finalize a plot:
    - Save to file if a path is provided
    - Optionally display the figure
    - Always close the figure to free memory
    """

    # Save image to disk
    if outpath is not None:
        fig.savefig(outpath, bbox_inches="tight", dpi=dpi)

    # Display figure if requested
    if show:
        plt.show()

    # Close figure to avoid memory issues when generating many plots
    plt.close(fig)


def _require_cols(df: pd.DataFrame, cols: Sequence[str]) -> None:
    """
    Validate that the dataframe contains required columns.
    Raises an error if any column is missing.
    """

    missing = [c for c in cols if c not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def plot_attacks_per_year(
    df,
    out_dir=None,
    filename="attacks_per_year.png",
    show=False,
    min_year=1900,
):
    """
    Line plot showing number of shark attacks per year.
    """

    # Ensure required column exists
    _require_cols(df, ["Year_final"])

    # Prepare output directory
    out_path = _ensure_outdir(out_dir)

    # Convert year column to numeric and remove invalid values
    years = pd.to_numeric(df["Year_final"], errors="coerce")

    # Filter by minimum year
    years = years[years >= min_year]

    # Count attacks per year
    s = years.value_counts().sort_index()

    fig = plt.figure()

    # Line plot
    plt.plot(s.index, s.values)

    plt.grid(alpha=0.3)

    plt.title(f"Shark attacks per year (>= {min_year})")
    plt.xlabel("Year")
    plt.ylabel("Count")

    # X-axis ticks every 20 years
    ticks = list(range(min_year, int(s.index.max()) + 1, 20))
    plt.xticks(ticks)

    _finalize(fig, out_path / filename if out_path else None, show=show)


def plot_attacks_by_month(
    df: pd.DataFrame,
    out_dir: Optional[str | Path] = None,
    filename: str = "attacks_by_month.png",
    show: bool = False,
    use_month_names: bool = True,
) -> None:
    """
    Bar plot showing number of attacks per month.
    Can use either month names or numeric month values.
    """

    _require_cols(df, ["Month", "Month_name"])

    out_path = _ensure_outdir(out_dir)

    if use_month_names:

        # Count attacks by month name
        s = df["Month_name"].fillna("Unknown").value_counts()

        # Reorder months to calendar order
        s = s.reindex(MONTH_ORDER).dropna()

        x = s.index.tolist()
        y = s.values

        fig = plt.figure()

        plt.bar(x, y)

        plt.title("Shark attacks by month")
        plt.xlabel("Month")
        plt.ylabel("Count")

        plt.xticks(rotation=45, ha="right")

    else:

        # Count attacks by numeric month
        s = df["Month"].dropna().astype(int).value_counts().sort_index()

        fig = plt.figure()

        plt.bar(s.index.astype(str), s.values)

        plt.title("Shark attacks by month")
        plt.xlabel("Month (1–12)")
        plt.ylabel("Count")

    _finalize(fig, out_path / filename if out_path else None, show=show)


def plot_attacks_by_time_category(
    df: pd.DataFrame,
    out_dir: Optional[str | Path] = None,
    filename: str = "attacks_by_time_category.png",
    show: bool = False,
) -> None:
    """
    Bar plot showing attacks by time-of-day category.
    """

    _require_cols(df, ["Time_category"])

    out_path = _ensure_outdir(out_dir)

    # Count attacks per category
    s = df["Time_category"].fillna("Unknown").value_counts()

    # Reorder categories logically
    s = s.reindex(TIME_CATEGORY_ORDER).fillna(0)

    fig = plt.figure()

    plt.bar(s.index, s.values)

    plt.title("Shark attacks by time of day")
    plt.xlabel("Time category")
    plt.ylabel("Count")

    plt.xticks(rotation=30, ha="right")

    _finalize(fig, out_path / filename if out_path else None, show=show)


def plot_fatal_vs_nonfatal(
    df: pd.DataFrame,
    out_dir: Optional[str | Path] = None,
    filename: str = "fatal_vs_nonfatal.png",
    show: bool = False,
) -> None:
    """
    Bar plot comparing fatal vs non-fatal attacks.
    """

    _require_cols(df, ["Fatal Y/N"])

    out_path = _ensure_outdir(out_dir)

    # Count attack outcomes
    s = df["Fatal Y/N"].fillna("Unknown").value_counts()

    fig = plt.figure()

    plt.bar(s.index, s.values)

    plt.title("Fatal vs Non-Fatal")
    plt.xlabel("Outcome")
    plt.ylabel("Count")

    plt.xticks(rotation=15, ha="right")

    _finalize(fig, out_path / filename if out_path else None, show=show)