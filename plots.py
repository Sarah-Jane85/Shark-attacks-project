# src/plots.py

# Expected columns (from shark_cleaning.py output):
#   Year_final, Month, Month_name, Time_category, Country, Fatal Y/N


from __future__ import annotations

from pathlib import Path
from typing import Optional, Sequence

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


MONTH_ORDER = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

TIME_CATEGORY_ORDER = ["Early morning", "Morning", "Afternoon", "Evening", "Night", "Unknown"]


def _ensure_outdir(out_dir: Optional[str | Path]) -> Optional[Path]:
    if out_dir is None:
        return None
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    return out_path


def _finalize(fig: plt.Figure, outpath: Optional[Path], show: bool = False, dpi: int = 150) -> None:
    if outpath is not None:
        fig.savefig(outpath, bbox_inches="tight", dpi=dpi)
    if show:
        plt.show()
    plt.close(fig)


def _require_cols(df: pd.DataFrame, cols: Sequence[str]) -> None:
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

    _require_cols(df, ["Year_final"])

    out_path = _ensure_outdir(out_dir)

    years = pd.to_numeric(df["Year_final"], errors="coerce")
    years = years[years >= min_year]

    s = years.value_counts().sort_index()

    fig = plt.figure()

    plt.plot(s.index, s.values)

    plt.grid(alpha=0.3)

    plt.title(f"Shark attacks per year (>= {min_year})")
    plt.xlabel("Year")
    plt.ylabel("Count")

    # Escala de 20 em 20 anos
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
    """Bar plot: attacks by month (calendar order)."""
    _require_cols(df, ["Month", "Month_name"])
    out_path = _ensure_outdir(out_dir)

    if use_month_names:
        s = df["Month_name"].fillna("Unknown").value_counts()
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
    """Bar plot: attacks by time-of-day category."""
    _require_cols(df, ["Time_category"])
    out_path = _ensure_outdir(out_dir)

    s = df["Time_category"].fillna("Unknown").value_counts()
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
    """Bar plot: fatal vs non-fatal counts."""
    _require_cols(df, ["Fatal Y/N"])
    out_path = _ensure_outdir(out_dir)

    s = df["Fatal Y/N"].fillna("Unknown").value_counts()

    fig = plt.figure()
    plt.bar(s.index, s.values)
    plt.title("Fatal vs Non-Fatal")
    plt.xlabel("Outcome")
    plt.ylabel("Count")
    plt.xticks(rotation=15, ha="right")

    _finalize(fig, out_path / filename if out_path else None, show=show)


def plot_attacks_by_month_and_outcome_stacked(
    df,
    out_dir=None,
    filename="attacks_by_month_outcome_stacked.png",
    show=False,
) -> None:
    """Stacked bar: month (calendar order) split by Non-Fatal / Fatal / Unknown."""
    _require_cols(df, ["Month_name", "Fatal Y/N"])
    out_path = _ensure_outdir(out_dir)

    # Build month x outcome table
    tmp = (
        df.assign(
            Month_name=df["Month_name"].fillna("Unknown"),
            **{"Fatal Y/N": df["Fatal Y/N"].fillna("Unknown")},
        )
        .groupby(["Month_name", "Fatal Y/N"])
        .size()
        .unstack(fill_value=0)
    )

    # Keep calendar months only and in order
    tmp = tmp.reindex(MONTH_ORDER).dropna(how="all")

    # Force a clean, consistent outcome order (ignore any unexpected categories)
    desired_cols = ["Non-Fatal", "Fatal", "Unknown"]
    tmp = tmp[[c for c in desired_cols if c in tmp.columns]]

    # Color palette (harmonious)
    color_map = {
        "Non-Fatal": "#90CAF9",  # light blue
        "Fatal": "#0D47A1",      # dark blue
        "Unknown": "#B0BEC5",    # bluish grey
    }

    fig = plt.figure()

    bottom = np.zeros(len(tmp.index))
    for col in tmp.columns:
        vals = tmp[col].values
        plt.bar(
            tmp.index,
            vals,
            bottom=bottom,
            label=col,
            color=color_map.get(col, None),
        )
        bottom = bottom + vals

    plt.title("Shark attacks by month (fatal and non-fatal)")
    plt.xlabel("Month")
    plt.ylabel("Count")
    plt.xticks(rotation=45, ha="right")
    plt.legend()

    _finalize(fig, out_path / filename if out_path else None, show=show)


def plot_top_countries(
    df: pd.DataFrame,
    top_n: int = 15,
    out_dir: Optional[str | Path] = None,
    filename: str = "top_countries.png",
    show: bool = False,
) -> None:
    """Horizontal bar: top N countries by number of attacks."""
    _require_cols(df, ["Country"])
    out_path = _ensure_outdir(out_dir)

    s = df["Country"].fillna("Unknown").value_counts().head(top_n)
    s = s.sort_values()  # for nicer horizontal bars (small->large top-to-bottom)

    fig = plt.figure()
    plt.barh(s.index, s.values)
    plt.title(f"Top {top_n} countries by attack count")
    plt.xlabel("Count")
    plt.ylabel("Country")

    _finalize(fig, out_path / filename if out_path else None, show=show)


def plot_heatmap_month_by_time(
    df: pd.DataFrame,
    out_dir: Optional[str | Path] = None,
    filename: str = "heatmap_month_by_time.png",
    show: bool = False,
) -> None:
    """Heatmap: Month (rows) x Time_category (cols) counts."""
    _require_cols(df, ["Month_name", "Time_category"])
    out_path = _ensure_outdir(out_dir)

    tmp = (
        df.assign(
            Month_name=df["Month_name"].fillna("Unknown"),
            Time_category=df["Time_category"].fillna("Unknown"),
        )
        .groupby(["Month_name", "Time_category"])
        .size()
        .unstack(fill_value=0)
    )

    # Restrict to real months for cleaner seasonality view
    tmp = tmp.reindex(MONTH_ORDER).dropna(how="all")
    tmp = tmp.reindex(columns=TIME_CATEGORY_ORDER, fill_value=0)

    fig = plt.figure()
    plt.imshow(tmp.values, aspect="auto")
    plt.title("Attacks heatmap: month vs time of day")
    plt.xlabel("Time category")
    plt.ylabel("Month")
    plt.xticks(ticks=np.arange(len(tmp.columns)), labels=tmp.columns, rotation=30, ha="right")
    plt.yticks(ticks=np.arange(len(tmp.index)), labels=tmp.index)

    # Annotate cells useful to keep light to avoid clutter for big values
    for i in range(tmp.shape[0]):
        for j in range(tmp.shape[1]):
            val = int(tmp.iloc[i, j])
            if val > 0:
                plt.text(j, i, str(val), ha="center", va="center")

    plt.colorbar(label="Count")

    _finalize(fig, out_path / filename if out_path else None, show=show)


def generate_all_figures(
    df: pd.DataFrame,
    out_dir: str | Path = "reports/figures",
    show: bool = False,
    top_countries_n: int = 15,
) -> None:
    """Convenience wrapper to generate a standard set of figures."""
    out_path = _ensure_outdir(out_dir)

    plot_attacks_per_year(df, out_dir=out_path, show=show)
    plot_attacks_by_month(df, out_dir=out_path, show=show)
    plot_attacks_by_time_category(df, out_dir=out_path, show=show)
    plot_fatal_vs_nonfatal(df, out_dir=out_path, show=show)
    plot_attacks_by_month_and_outcome_stacked(df, out_dir=out_path, show=show)
    plot_top_countries(df, top_n=top_countries_n, out_dir=out_path, show=show)
    plot_heatmap_month_by_time(df, out_dir=out_path, show=show)