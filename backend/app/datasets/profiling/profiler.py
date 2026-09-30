from typing import Any, Dict, List, Optional
import math
import re
from datetime import datetime, timezone
import pandas as pd
import numpy as np
from app.datasets.profiling.quality_scorer import QualityScorer


class DatasetProfiler:
    """
    Analyzes dataset records and generates comprehensive column-level profiling statistics,
    distribution histograms, and quality reports.
    """

    @classmethod
    def profile_dataset(
        cls,
        records: List[Dict[str, Any]],
        schema_fields: Optional[List[Dict[str, Any]]] = None,
        sources_count: int = 0,
        provenance_count: int = 0,
        dataset_meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        schema_fields = schema_fields or []
        dataset_meta = dataset_meta or {}
        total_records = len(records)

        # Build normalized rows DataFrame
        rows_data = []
        for r in records:
            data = r.get("record_data") or r.get("data") or r
            if isinstance(data, dict):
                rows_data.append(data)
            else:
                rows_data.append({})

        df = pd.DataFrame(rows_data) if rows_data else pd.DataFrame()

        # Identify all columns (merge from schema and dataframe)
        schema_col_map = {f.get("name"): f for f in schema_fields if f.get("name")}
        df_cols = list(df.columns) if not df.empty else []
        all_col_names = []
        for c in schema_col_map.keys():
            if c not in all_col_names:
                all_col_names.append(c)
        for c in df_cols:
            if c not in all_col_names:
                all_col_names.append(c)

        # 1. Column-Level Statistics
        columns_profile = []
        for col_name in all_col_names:
            field_def = schema_col_map.get(col_name, {})
            display_label = field_def.get("description") or col_name.replace("_", " ").title()
            configured_type = field_def.get("type", "string")

            if df.empty or col_name not in df.columns:
                columns_profile.append({
                    "column_name": col_name,
                    "display_label": display_label,
                    "inferred_type": configured_type,
                    "non_null_count": 0,
                    "null_count": total_records,
                    "missing_percentage": 100.0,
                    "unique_count": 0,
                    "duplicate_count": 0,
                    "min_value": None,
                    "max_value": None,
                    "mean": None,
                    "median": None,
                    "top_values": [],
                    "string_length_stats": None,
                    "valid_format_percentage": 0.0,
                    "sample_values": [],
                })
                continue

            series = df[col_name]
            # Replace empty strings and 'null' strings with None
            cleaned_series = series.apply(
                lambda x: None if (pd.isna(x) or str(x).strip() == "" or str(x).strip().lower() == "null") else x
            )

            non_null_count = int(cleaned_series.notna().sum())
            null_count = int(total_records - non_null_count)
            missing_pct = round((null_count / max(total_records, 1)) * 100.0, 1)

            valid_values = cleaned_series.dropna().tolist()
            unique_values = len(set([str(v) for v in valid_values]))
            duplicate_values_count = max(0, len(valid_values) - unique_values)

            # Inferred type check
            inferred_type = configured_type
            numeric_stats = {"min": None, "max": None, "mean": None, "median": None}
            str_length_stats = None
            valid_format_pct = 100.0

            # Check if numeric
            numeric_vals = []
            for v in valid_values:
                try:
                    if isinstance(v, (int, float)) and not isinstance(v, bool):
                        numeric_vals.append(float(v))
                    elif isinstance(v, str):
                        cleaned_num = re.sub(r"[^\d.-]", "", v)
                        if cleaned_num and cleaned_num not in ["-", "."]:
                            numeric_vals.append(float(cleaned_num))
                except Exception:
                    pass

            if len(numeric_vals) >= max(1, int(0.7 * len(valid_values))) and len(valid_values) > 0:
                if configured_type in ["number", "integer", "float"] or (configured_type == "string" and len(numeric_vals) == len(valid_values)):
                    inferred_type = "number"
                    numeric_stats["min"] = round(float(np.min(numeric_vals)), 2)
                    numeric_stats["max"] = round(float(np.max(numeric_vals)), 2)
                    numeric_stats["mean"] = round(float(np.mean(numeric_vals)), 2)
                    numeric_stats["median"] = round(float(np.median(numeric_vals)), 2)

            # String length stats
            str_vals = [str(v) for v in valid_values]
            if str_vals and inferred_type != "number":
                lens = [len(s) for s in str_vals]
                str_length_stats = {
                    "min_len": int(np.min(lens)),
                    "max_len": int(np.max(lens)),
                    "avg_len": round(float(np.mean(lens)), 1),
                }

            # URL validation stats
            if "url" in col_name.lower() or configured_type == "url":
                inferred_type = "url"
                valid_url_count = sum(1 for s in str_vals if s.startswith("http://") or s.startswith("https://"))
                valid_format_pct = round((valid_url_count / max(len(str_vals), 1)) * 100.0, 1)

            # Top frequent values
            val_counts = pd.Series(str_vals).value_counts().head(5)
            top_values = [
                {"value": str(val), "count": int(cnt), "percentage": round((int(cnt) / max(total_records, 1)) * 100.0, 1)}
                for val, cnt in val_counts.items()
            ]

            # Sample values (first 5 unique)
            sample_values = list(dict.fromkeys(str_vals))[:5]

            columns_profile.append({
                "column_name": col_name,
                "display_label": display_label,
                "inferred_type": inferred_type,
                "non_null_count": non_null_count,
                "null_count": null_count,
                "missing_percentage": missing_pct,
                "unique_count": unique_values,
                "duplicate_count": duplicate_values_count,
                "min_value": numeric_stats["min"],
                "max_value": numeric_stats["max"],
                "mean": numeric_stats["mean"],
                "median": numeric_stats["median"],
                "top_values": top_values,
                "string_length_stats": str_length_stats,
                "valid_format_percentage": valid_format_pct,
                "sample_values": sample_values,
            })

        # 2. Quality Scores
        quality_results = QualityScorer.calculate_quality(
            records=records,
            schema_fields=schema_fields,
            sources_count=sources_count,
            provenance_count=provenance_count,
        )

        # 3. Overall Record Summary
        valid_count = sum(1 for r in records if r.get("validation_status") == "valid")
        warning_count = sum(1 for r in records if r.get("validation_status") == "valid_with_warnings")
        invalid_count = sum(1 for r in records if r.get("validation_status") == "invalid")
        duplicate_count = quality_results["dimensions"]["uniqueness"]["affected_count"]
        unique_records_count = max(0, total_records - duplicate_count)

        overview = {
            "total_records": total_records,
            "total_columns": len(all_col_names),
            "total_sources": sources_count,
            "valid_records": valid_count,
            "records_with_warnings": warning_count,
            "invalid_records": invalid_count,
            "duplicate_records": duplicate_count,
            "unique_records": unique_records_count,
            "created_at": dataset_meta.get("created_at") or datetime.now(timezone.utc).isoformat(),
            "updated_at": dataset_meta.get("updated_at") or datetime.now(timezone.utc).isoformat(),
        }

        return {
            "overview": overview,
            "columns": columns_profile,
            "quality": quality_results,
            "profiled_at": datetime.now(timezone.utc).isoformat(),
        }
