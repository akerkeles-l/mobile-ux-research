
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent.parent

RAW_CSV = ROOT / "data" / "sample" / "sample_data.csv"
PROCESSED_CSV = ROOT / "data" / "processed" / "metrics_summary.csv"

OUTPUT_DIR = ROOT / "reports" / "figures"


def load_data():
    if RAW_CSV.exists():
        data = pd.read_csv(RAW_CSV)
    elif PROCESSED_CSV.exists():
        data = pd.read_csv(PROCESSED_CSV)
    else:
        raise FileNotFoundError(
            "No input CSV found. Check data/sample or data/processed."
        )

    required_columns = {"interface", "task_time_seconds"}

    if RAW_CSV.exists() and not required_columns.issubset(data.columns):
        raise ValueError(
            "Raw CSV must contain interface and task_time_seconds columns."
        )

    if not RAW_CSV.exists():
        raise ValueError(
            "The processed summary does not contain individual observations. "
            "A raw dataset is required for the boxplot."
        )

    data = data.dropna(subset=["interface", "task_time_seconds"])
    data["task_time_seconds"] = pd.to_numeric(
        data["task_time_seconds"], errors="coerce"
    )
    data = data.dropna(subset=["task_time_seconds"])

    data = data[
        data["interface"].isin(["baseline", "improved"])
    ]

    if data.empty:
        raise ValueError("No valid Baseline or Improved observations found.")

    return data


def save_figure(fig, filename):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fig.savefig(OUTPUT_DIR / f"{filename}.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUTPUT_DIR / f"{filename}.pdf", bbox_inches="tight")

    plt.close(fig)


def create_latency_chart(data):
    summary = (
        data.groupby("interface")["task_time_seconds"]
        .mean()
        .reindex(["baseline", "improved"])
    )

    fig, ax = plt.subplots(figsize=(8, 5))

    summary.plot(kind="bar", ax=ax)

    ax.set_title("Task Completion Time by Interface")
    ax.set_xlabel("Interface Version")
    ax.set_ylabel("Average Task Time (seconds)")
    ax.set_xticklabels(["Baseline", "Improved"], rotation=0)

    ax.grid(axis="y", linestyle="--", alpha=0.4)

    fig.tight_layout()

    save_figure(fig, "fig1_latency_vs_load")


def create_distribution_boxplot(data):
    baseline = data.loc[
        data["interface"] == "baseline", "task_time_seconds"
    ]

    improved = data.loc[
        data["interface"] == "improved", "task_time_seconds"
    ]

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.boxplot(
        [baseline, improved],
        tick_labels=["Baseline", "Improved"]
    )

    ax.set_title("Distribution of Task Completion Time")
    ax.set_xlabel("Interface Version")
    ax.set_ylabel("Task Time (seconds)")

    ax.grid(axis="y", linestyle="--", alpha=0.4)

    fig.tight_layout()

    save_figure(fig, "fig2_distribution_boxplot")


def main():
    data = load_data()

    create_latency_chart(data)
    create_distribution_boxplot(data)

    print("Visualizations were successfully created.")
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
