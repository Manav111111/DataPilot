import re
from typing import Any, Dict, List, Optional
from collections import defaultdict
import numpy as np
import pandas as pd


class DatasetAnalyticsService:
    """
    Computes statistical distributions, dynamic aggregations, and chart data points
    for interactive Recharts dashboards based strictly on real dataset records.
    """

    @classmethod
    def get_field_distributions(
        cls,
        records: List[Dict[str, Any]],
        field_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        if not records:
            return {"distributions": {}}

        rows_data = []
        for r in records:
            data = r.get("record_data") or r.get("data") or r
            if isinstance(data, dict):
                rows_data.append(data)

        df = pd.DataFrame(rows_data) if rows_data else pd.DataFrame()
        if df.empty:
            return {"distributions": {}}

        cols_to_analyze = field_names or list(df.columns)
        distributions = {}

        for col in cols_to_analyze:
            if col not in df.columns:
                continue

            series = df[col].dropna()
            clean_series = series[series.apply(lambda x: str(x).strip() != "" and str(x).strip().lower() != "null")]

            if clean_series.empty:
                distributions[col] = {"type": "empty", "data": []}
                continue

            # Try numeric distribution
            numeric_vals = []
            for v in clean_series:
                try:
                    if isinstance(v, (int, float)) and not isinstance(v, bool):
                        numeric_vals.append(float(v))
                    elif isinstance(v, str):
                        cleaned_num = re.sub(r"[^\d.-]", "", v)
                        if cleaned_num and cleaned_num not in ["-", "."]:
                            numeric_vals.append(float(cleaned_num))
                except Exception:
                    pass

            if len(numeric_vals) >= max(1, int(0.8 * len(clean_series))):
                # Numeric histogram bins (up to 8 bins)
                arr = np.array(numeric_vals)
                min_v, max_v = float(np.min(arr)), float(np.max(arr))
                if min_v == max_v:
                    distributions[col] = {
                        "type": "numeric",
                        "data": [{"bin": f"{min_v:.0f}", "count": len(numeric_vals), "min": min_v, "max": max_v}],
                    }
                else:
                    counts, bin_edges = np.histogram(arr, bins=min(8, len(set(numeric_vals))))
                    bin_data = []
                    for i in range(len(counts)):
                        b_start = bin_edges[i]
                        b_end = bin_edges[i + 1]
                        label = f"{b_start:,.0f} - {b_end:,.0f}" if b_end > 100 else f"{b_start:.1f} - {b_end:.1f}"
                        bin_data.append({
                            "bin": label,
                            "count": int(counts[i]),
                            "min": float(b_start),
                            "max": float(b_end),
                        })
                    distributions[col] = {"type": "numeric", "data": bin_data}
                continue

            # Categorical distribution
            top_counts = clean_series.astype(str).value_counts().head(10)
            cat_data = [
                {"category": str(k), "count": int(v)}
                for k, v in top_counts.items()
            ]
            distributions[col] = {"type": "categorical", "data": cat_data}

        return {"distributions": distributions}

    @classmethod
    def compute_chart_data(
        cls,
        records: List[Dict[str, Any]],
        chart_type: str,
        configuration: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Executes dynamic grouping and aggregation for Recharts visual rendering.
        Supported aggregations: count, sum, avg, min, max, distinct_count.
        """
        if not records:
            return {"chart_type": chart_type, "data": [], "empty_reason": "No records in dataset."}

        x_field = configuration.get("x_field")
        y_field = configuration.get("y_field")
        agg = configuration.get("aggregation", "count").lower()
        group_by = configuration.get("group_by")
        max_items = int(configuration.get("max_items", 15))

        if not x_field:
            return {"chart_type": chart_type, "data": [], "empty_reason": "Missing required 'x_field' configuration."}

        rows_data = []
        for r in records:
            data = r.get("record_data") or r.get("data") or r
            if isinstance(data, dict):
                rows_data.append(data)

        df = pd.DataFrame(rows_data)
        if df.empty or x_field not in df.columns:
            return {"chart_type": chart_type, "data": [], "empty_reason": f"Field '{x_field}' has no data."}

        # Filter out null x_field values
        df_clean = df[df[x_field].notna()].copy()
        df_clean[x_field] = df_clean[x_field].astype(str)

        # 1. Grouped Aggregation
        if agg == "count":
            counts = df_clean[x_field].value_counts().head(max_items)
            chart_data = [{"name": str(k), "value": int(v), "count": int(v)} for k, v in counts.items()]

        elif agg in ["sum", "avg", "min", "max"]:
            if not y_field or y_field not in df.columns:
                # Fallback to count
                counts = df_clean[x_field].value_counts().head(max_items)
                chart_data = [{"name": str(k), "value": int(v)} for k, v in counts.items()]
            else:
                # Parse numeric y_field
                def clean_num(val):
                    try:
                        num = re.sub(r"[^\d.-]", "", str(val))
                        return float(num) if num and num not in ["-", "."] else None
                    except Exception:
                        return None

                df_clean["__y_num"] = df_clean[y_field].apply(clean_num)
                grouped = df_clean.groupby(x_field)["__y_num"].agg(
                    "sum" if agg == "sum" else ("mean" if agg == "avg" else agg)
                ).dropna()

                sorted_grouped = grouped.sort_values(ascending=False).head(max_items)
                chart_data = [
                    {"name": str(k), "value": round(float(v), 2), y_field: round(float(v), 2)}
                    for k, v in sorted_grouped.items()
                ]

        elif agg == "distinct_count":
            if not y_field or y_field not in df.columns:
                counts = df_clean[x_field].nunique()
                chart_data = [{"name": x_field, "value": int(counts)}]
            else:
                grouped = df_clean.groupby(x_field)[y_field].nunique()
                sorted_grouped = grouped.sort_values(ascending=False).head(max_items)
                chart_data = [{"name": str(k), "value": int(v)} for k, v in sorted_grouped.items()]
        else:
            counts = df_clean[x_field].value_counts().head(max_items)
            chart_data = [{"name": str(k), "value": int(v)} for k, v in counts.items()]

        return {
            "chart_name": configuration.get("chart_name", f"{x_field.replace('_', ' ').title()} Analysis"),
            "chart_type": chart_type,
            "x_field": x_field,
            "y_field": y_field,
            "aggregation": agg,
            "data": chart_data,
        }
