from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def build_pareto(df: pd.DataFrame, category_col: str, impact_col: str) -> pd.DataFrame:
    grouped = (
        df.groupby(category_col, dropna=False)[impact_col]
        .sum()
        .reset_index()
        .sort_values(impact_col, ascending=False)
    )
    total = grouped[impact_col].sum() if not grouped.empty else 0
    grouped["cumulative"] = grouped[impact_col].cumsum()
    grouped["cumulative_pct"] = (grouped["cumulative"] / total * 100).round(2) if total > 0 else 0
    grouped["vital_few"] = grouped["cumulative_pct"] <= 80
    if not grouped.empty and not grouped["vital_few"].any():
        grouped.loc[grouped.index[0], "vital_few"] = True
    return grouped


def save_pareto_chart(pareto_df: pd.DataFrame, category_col: str, impact_col: str, output_path: str | Path) -> str:
    output_path = str(output_path)
    fig, ax = plt.subplots(figsize=(4.2, 2.6))
    ax.bar(pareto_df[category_col].astype(str), pareto_df[impact_col], color="#4C78A8")
    ax.set_ylabel("Impact")
    ax.tick_params(axis="x", rotation=35)

    ax2 = ax.twinx()
    ax2.plot(pareto_df[category_col].astype(str), pareto_df["cumulative_pct"], color="#F58518", marker="o")
    ax2.set_ylim(0, 100)
    ax2.set_ylabel("Cum %")
    ax2.axhline(80, color="#54A24B", linestyle="--", linewidth=1)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return output_path
