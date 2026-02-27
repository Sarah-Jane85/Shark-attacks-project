# main.py
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from shark_cleaning import run_pipeline, CleaningConfig
from plots import generate_all_figures


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Clean Shark Attacks dataset + generate plots.")
    p.add_argument("--raw", default="Shark_Attacks.xls", help="Path to raw Excel (.xls/.xlsx)")
    p.add_argument("--clean-out", default="shark_attacks_clean.csv", help="Output cleaned CSV")
    p.add_argument("--cube-out", default="seasonality_analysis.csv", help="Output cube CSV")
    p.add_argument("--figdir", default="figures", help="Directory for PNG figures")
    p.add_argument("--no-plots", action="store_true", help="Skip plot generation")
    p.add_argument("--show", action="store_true", help="Show plots interactively (also saves)")
    p.add_argument("--top-countries", type=int, default=15, help="Top N countries for the chart")
    p.add_argument("--keep-invalid-dates", action="store_true", help="Do not drop rows with invalid dates")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    raw_path = Path(args.raw)
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw file not found: {raw_path.resolve()}")

    # Read excel
    df = pd.read_excel(raw_path)

    # Run cleaning
    cfg = CleaningConfig(drop_invalid_dates=not args.keep_invalid_dates)
    df_clean, cube, report = run_pipeline(df, cfg=cfg, return_cube=True)

    # Save outputs (same folder, simple)
    Path(args.clean_out).write_text("", encoding="utf-8")  # ensures path is writable early
    df_clean.to_csv(args.clean_out, index=False)

    if cube is not None:
        cube.to_csv(args.cube_out, index=False)

    print("Cleaning complete")
    print(f"Initial rows: {report.get('initial_rows')}")
    print(f"Final rows:   {report.get('final_rows')}")
    if "cube" in report:
        print(f"Cube ok:      {report['cube'].get('cube_integrity_ok')}")

    # Plots
    if not args.no_plots:
        figdir = Path(args.figdir)
        figdir.mkdir(parents=True, exist_ok=True)

        generate_all_figures(
            df_clean,
            out_dir=figdir,
            show=args.show,
            top_countries_n=args.top_countries,
        )
        print(f"Figures saved to: {figdir.resolve()}")


if __name__ == "__main__":
    main()