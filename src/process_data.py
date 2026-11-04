import json
from pathlib import Path

import numpy as np
import pandas as pd


np.random.seed(42)

ROOT = Path(__file__).resolve().parent.parent

RAW_FILE = ROOT / "data" / "raw" / "test_run.jsonl"
OUTPUT_FILE = ROOT / "data" / "processed" / "metrics_summary.csv"

BOOTSTRAP_ITERATIONS = 5000


def load_data():
    """Load JSONL records into a DataFrame."""
    records = []

    with open(RAW_FILE, "r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                records.append(json.loads(line))

    return pd.DataFrame(records)


def bootstrap_mean_ci(values, iterations=BOOTSTRAP_ITERATIONS):
    """Calculate a bootstrap 95% confidence interval for the mean."""
    values = np.asarray(values, dtype=float)

    if len(values) == 0:
        return np.nan, np.nan

    rng = np.random.default_rng(42)

    bootstrap_means = [
        np.mean(rng.choice(values, size=len(values), replace=True))
        for _ in range(iterations)
    ]

    lower = np.percentile(bootstrap_means, 2.5)
    upper = np.percentile(bootstrap_means, 97.5)

    return lower, upper


def process_data():
    df = load_data()

    required_columns = [
        "user_id",
        "interface",
        "run_type",
        "task_time_seconds",
        "task_success",
        "error_count",
        "satisfaction",
    ]

    missing = set(required_columns) - set(df.columns)

    if missing:
        raise ValueError(f"Missing columns: {missing}")

    # Keep evaluation records only; exclude warm-up records.
    df = df[df["run_type"] == "evaluation"].copy()

    # Convert metric columns to numeric values.
    numeric_columns = [
        "task_time_seconds",
        "task_success",
        "error_count",
        "satisfaction",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    # Remove incomplete or invalid rows.
    df = df.dropna(subset=required_columns)

    df = df[
        (df["task_time_seconds"] > 0)
        & (df["task_success"].isin([0, 1]))
        & (df["error_count"] >= 0)
        & (df["satisfaction"].between(1, 5))
        & (df["interface"].isin(["baseline", "improved"]))
    ]

    if df.empty:
        raise ValueError("No valid evaluation records found.")

    results = []

    for interface, group in df.groupby("interface"):
        times = group["task_time_seconds"].to_numpy()

        ci_lower, ci_upper = bootstrap_mean_ci(times)

        results.append({
            "interface": interface,
            "n": len(group),
            "mean_task_time_seconds": times.mean(),
            "median_task_time_seconds": np.median(times),
            "p95_task_time_seconds": np.percentile(times, 95),
            "p99_task_time_seconds": np.percentile(times, 99),
            "task_time_ci95_lower": ci_lower,
            "task_time_ci95_upper": ci_upper,
            "task_success_rate": group["task_success"].mean(),
            "error_rate": (group["error_count"] > 0).mean(),
            "mean_error_count": group["error_count"].mean(),
            "mean_satisfaction": group["satisfaction"].mean(),
        })

    summary = pd.DataFrame(results)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUTPUT_FILE, index=False)

    print("Data processing completed.")
    print(f"Evaluation records: {len(df)}")
    print(f"Saved results to: {OUTPUT_FILE}")
    print()
    print(summary.to_string(index=False))


if __name__ == "__main__":
    process_data()