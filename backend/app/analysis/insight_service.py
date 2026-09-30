import logging
import math
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from app.schemas.analysis import (
    AutoInsightsResponse,
    InsightItem,
    ChartConfig,
)
from app.analysis.query_executor import sanitize_for_json

logger = logging.getLogger(__name__)


class InsightService:
    @staticmethod
    def generate_auto_insights(
        df: pd.DataFrame, dataset_id: str, dataset_name: str, dataset_version: int
    ) -> AutoInsightsResponse:
        """
        Scans a dataset and generates structured, verified insight cards.
        All numbers are computed from actual records.
        """
        insights: List[InsightItem] = []
        row_count = len(df)

        if df.empty or row_count == 0:
            return AutoInsightsResponse(
                dataset_id=dataset_id,
                dataset_name=dataset_name,
                dataset_version=dataset_version,
                record_count=0,
                insights=[
                    InsightItem(
                        title="Empty Dataset",
                        category="overview",
                        explanation="The dataset currently contains no records to analyze.",
                        evidence={"row_count": 0},
                        columns=[],
                        method="record_count",
                    )
                ],
            )

        # 1. Dataset Dimensions & Completeness Overview
        total_cells = row_count * len(df.columns)
        null_cells = int(df.isna().sum().sum() + (df == "").sum().sum())
        completeness_pct = round(((total_cells - null_cells) / total_cells) * 100, 1) if total_cells > 0 else 0

        insights.append(
            InsightItem(
                title=f"Dataset Scale & Health: {row_count} Records Across {len(df.columns)} Columns",
                category="overview",
                explanation=(
                    f"The '{dataset_name}' dataset contains {row_count} records and {len(df.columns)} columns "
                    f"with an overall data completeness score of {completeness_pct}%."
                ),
                evidence={
                    "total_records": row_count,
                    "total_columns": len(df.columns),
                    "completeness_pct": completeness_pct,
                    "null_cells_count": null_cells,
                },
                columns=list(df.columns),
                method="descriptive_scale",
                suggested_followup="Show me a breakdown of missing values across all columns.",
            )
        )

        # 2. Key Numeric Metrics & Extremes
        numeric_cols = []
        for col in df.columns:
            s = pd.to_numeric(df[col], errors="coerce")
            if s.notna().sum() >= max(3, int(row_count * 0.4)):
                numeric_cols.append(col)

        for num_col in numeric_cols[:2]:
            series = pd.to_numeric(df[num_col], errors="coerce").dropna()
            if len(series) >= 2:
                max_val = float(series.max())
                min_val = float(series.min())
                mean_val = float(series.mean())
                median_val = float(series.median())

                # Find entity with max val
                max_idx = series.idxmax()
                entity_label = ""
                for cat in df.columns:
                    if cat != num_col and df[cat].dtype == object:
                        entity_label = str(df.loc[max_idx, cat])
                        break

                explanation = (
                    f"'{num_col}' averages {sanitize_for_json(mean_val)} (median {sanitize_for_json(median_val)}), "
                    f"spanning from a minimum of {sanitize_for_json(min_val)} to a peak of {sanitize_for_json(max_val)}."
                )
                if entity_label:
                    explanation += f" Top record is '{entity_label}' with {sanitize_for_json(max_val)}."

                insights.append(
                    InsightItem(
                        title=f"Highest & Lowest {num_col.replace('_', ' ').title()}",
                        category="extremes",
                        explanation=explanation,
                        evidence={
                            "column": num_col,
                            "max": sanitize_for_json(max_val),
                            "min": sanitize_for_json(min_val),
                            "mean": sanitize_for_json(mean_val),
                            "median": sanitize_for_json(median_val),
                            "top_entity": entity_label or None,
                        },
                        columns=[num_col],
                        method="numerical_extremes",
                        suggested_followup=f"Show the top 5 records by {num_col}.",
                    )
                )

        # 3. Categorical Patterns & Dominant Segments
        categorical_cols = [c for c in df.columns if c not in numeric_cols and df[c].nunique() > 1 and df[c].nunique() < row_count]
        for cat_col in categorical_cols[:2]:
            counts = df[cat_col].value_counts().head(5)
            if not counts.empty:
                top_cat = str(counts.index[0])
                top_count = int(counts.iloc[0])
                top_pct = round((top_count / row_count) * 100, 1)

                chart_data = [{"name": str(k), "value": int(v)} for k, v in counts.items()]

                insights.append(
                    InsightItem(
                        title=f"Dominant Category in {cat_col.replace('_', ' ').title()}: '{top_cat}'",
                        category="categorical",
                        explanation=(
                            f"'{top_cat}' represents the largest segment in '{cat_col}' with {top_count} records "
                            f"({top_pct}% of total records)."
                        ),
                        evidence={
                            "column": cat_col,
                            "top_category": top_cat,
                            "top_count": top_count,
                            "top_percentage": top_pct,
                            "distinct_categories": int(df[cat_col].nunique()),
                        },
                        columns=[cat_col],
                        method="frequency_distribution",
                        chart_data=chart_data,
                        chart_config=ChartConfig(
                            chart_type="pie",
                            x_axis="name",
                            y_axis="value",
                            title=f"Distribution of {cat_col.replace('_', ' ').title()}",
                        ),
                        suggested_followup=f"Compare average metrics grouped by {cat_col}.",
                    )
                )

        # 4. Outliers & Anomalies
        for num_col in numeric_cols[:2]:
            series = pd.to_numeric(df[num_col], errors="coerce").dropna()
            if len(series) >= 6:
                q1 = float(series.quantile(0.25))
                q3 = float(series.quantile(0.75))
                iqr = q3 - q1
                if iqr > 0:
                    lower = q1 - 1.5 * iqr
                    upper = q3 + 1.5 * iqr
                    outliers = series[(series < lower) | (series > upper)]
                    if len(outliers) > 0:
                        outlier_pct = round((len(outliers) / len(series)) * 100, 1)
                        insights.append(
                            InsightItem(
                                title=f"Statistical Outliers Detected in {num_col.replace('_', ' ').title()}",
                                category="outlier",
                                explanation=(
                                    f"Detected {len(outliers)} statistical outlier(s) ({outlier_pct}%) in '{num_col}' "
                                    f"exceeding normal IQR boundaries [{sanitize_for_json(lower)} to {sanitize_for_json(upper)}]."
                                ),
                                evidence={
                                    "column": num_col,
                                    "outlier_count": len(outliers),
                                    "lower_bound": sanitize_for_json(lower),
                                    "upper_bound": sanitize_for_json(upper),
                                    "sample_outlier_values": [sanitize_for_json(v) for v in outliers.head(3).tolist()],
                                },
                                columns=[num_col],
                                method="interquartile_range_iqr",
                                suggested_followup=f"Which records are outliers in {num_col}?",
                            )
                        )

        # 5. Correlations
        if len(numeric_cols) >= 2:
            num_df = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
            corr = num_df.corr().round(3)
            for i in range(len(numeric_cols)):
                for j in range(i + 1, len(numeric_cols)):
                    c1 = numeric_cols[i]
                    c2 = numeric_cols[j]
                    r_val = float(corr.loc[c1, c2])
                    if not math.isnan(r_val) and abs(r_val) >= 0.4:
                        rel = "positive" if r_val > 0 else "negative"
                        strength = "strong" if abs(r_val) >= 0.7 else "moderate"
                        insights.append(
                            InsightItem(
                                title=f"Correlation: {c1.title()} & {c2.title()} (r = {r_val})",
                                category="correlation",
                                explanation=(
                                    f"There is a {strength} {rel} linear relationship between '{c1}' and '{c2}' "
                                    f"with a Pearson correlation coefficient of {r_val}."
                                ),
                                evidence={"column_a": c1, "column_b": c2, "pearson_r": r_val, "strength": strength},
                                columns=[c1, c2],
                                method="pearson_correlation",
                                suggested_followup=f"Show scatter plot between {c1} and {c2}.",
                            )
                        )

        # 6. Quality & Missing Data Alerts
        for col in df.columns:
            null_cnt = int(df[col].isna().sum() + (df[col] == "").sum())
            null_pct = round((null_cnt / row_count) * 100, 1)
            if null_pct >= 25.0:
                insights.append(
                    InsightItem(
                        title=f"Data Quality Alert: High Missing Rate in '{col}' ({null_pct}%)",
                        category="quality",
                        explanation=(
                            f"Column '{col}' is missing values in {null_cnt} records ({null_pct}% of dataset). "
                            "Consider applying data cleaning or default imputation before relying on this field."
                        ),
                        evidence={"column": col, "missing_count": null_cnt, "missing_percentage": null_pct},
                        columns=[col],
                        method="missing_value_audit",
                        suggested_followup=f"Filter records where {col} is missing.",
                    )
                )

        return AutoInsightsResponse(
            dataset_id=dataset_id,
            dataset_name=dataset_name,
            dataset_version=dataset_version,
            record_count=row_count,
            insights=insights,
        )
