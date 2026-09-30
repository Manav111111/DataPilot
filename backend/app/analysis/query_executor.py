import logging
import math
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from app.schemas.analysis import (
    AnalyticalQueryPlan,
    QueryExecutionResult,
    QueryResultTable,
    ChartConfig,
)

logger = logging.getLogger(__name__)


def sanitize_for_json(val: Any) -> Any:
    """Recursively ensures numbers and values are JSON-serializable."""
    if val is None:
        return None
    if isinstance(val, (int, bool, str)):
        return val
    if isinstance(val, (float, np.floating)):
        if math.isnan(val) or math.isinf(val):
            return None
        return round(float(val), 4)
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (pd.Timestamp, np.datetime64)):
        return str(val)
    if isinstance(val, dict):
        return {k: sanitize_for_json(v) for k, v in val.items()}
    if isinstance(val, (list, tuple, set)):
        return [sanitize_for_json(v) for v in val]
    return str(val)


class QueryExecutor:
    @staticmethod
    def execute(df: pd.DataFrame, plan: AnalyticalQueryPlan) -> QueryExecutionResult:
        """
        Safely executes the validated analytical query plan on the DataFrame.
        """
        if df.empty:
            return QueryExecutionResult(
                table=QueryResultTable(columns=[], rows=[], total_rows=0),
                metrics={"status": "empty_dataset", "total_records": 0},
                computation_summary="Dataset contains no records to analyze.",
                row_count_analyzed=0,
            )

        working_df = df.copy()

        # Step 1: Apply Filters
        working_df = QueryExecutor._apply_filters(working_df, plan.filters)
        row_count_after_filter = len(working_df)

        # Step 2: Route by operation
        op = plan.operation

        if op == "group_by":
            return QueryExecutor._execute_group_by(working_df, plan, row_count_after_filter)
        elif op == "aggregate":
            return QueryExecutor._execute_aggregate(working_df, plan, row_count_after_filter)
        elif op == "sort_limit":
            return QueryExecutor._execute_sort_limit(working_df, plan, row_count_after_filter)
        elif op == "distribution":
            return QueryExecutor._execute_distribution(working_df, plan, row_count_after_filter)
        elif op == "outlier_detection":
            return QueryExecutor._execute_outliers(working_df, plan, row_count_after_filter)
        elif op == "correlation":
            return QueryExecutor._execute_correlation(working_df, plan, row_count_after_filter)
        elif op == "missing_analysis":
            return QueryExecutor._execute_missing_analysis(working_df, plan, row_count_after_filter)
        else:
            return QueryExecutor._execute_general_summary(working_df, plan, row_count_after_filter)

    @staticmethod
    def _apply_filters(df: pd.DataFrame, filters: List[Any]) -> pd.DataFrame:
        filtered_df = df
        for f in filters:
            col = f.column
            if col not in filtered_df.columns:
                continue
            op = f.operator
            val = f.value

            if op == "is_null":
                filtered_df = filtered_df[filtered_df[col].isna()]
            elif op == "is_not_null":
                filtered_df = filtered_df[filtered_df[col].notna()]
            elif op == "==":
                filtered_df = filtered_df[filtered_df[col] == val]
            elif op == "!=":
                filtered_df = filtered_df[filtered_df[col] != val]
            elif op == "contains" and val is not None:
                filtered_df = filtered_df[
                    filtered_df[col].astype(str).str.contains(str(val), case=False, na=False)
                ]
            elif op in (">", "<", ">=", "<="):
                # Convert to numeric for comparison if numeric
                series = pd.to_numeric(filtered_df[col], errors="coerce")
                try:
                    num_val = float(val)
                    if op == ">":
                        filtered_df = filtered_df[series > num_val]
                    elif op == "<":
                        filtered_df = filtered_df[series < num_val]
                    elif op == ">=":
                        filtered_df = filtered_df[series >= num_val]
                    elif op == "<=":
                        filtered_df = filtered_df[series <= num_val]
                except (ValueError, TypeError):
                    pass
        return filtered_df

    @staticmethod
    def _execute_group_by(
        df: pd.DataFrame, plan: AnalyticalQueryPlan, total_rows: int
    ) -> QueryExecutionResult:
        group_col = plan.group_by_column or (plan.target_columns[0] if plan.target_columns else df.columns[0])
        val_col = (
            plan.target_columns[0]
            if plan.target_columns and plan.target_columns[0] != group_col
            else None
        )
        agg_func = plan.aggregation_func or "count"

        if val_col and val_col in df.columns and agg_func != "count":
            num_series = pd.to_numeric(df[val_col], errors="coerce")
            temp_df = df.copy()
            temp_df[val_col] = num_series

            if agg_func in ("sum", "mean", "median", "min", "max"):
                grouped = getattr(temp_df.groupby(group_col)[val_col], agg_func)()
            else:
                grouped = temp_df.groupby(group_col)[val_col].count()
        else:
            grouped = df.groupby(group_col).size()
            val_col = "count"

        result_df = grouped.reset_index()
        metric_col_name = f"{agg_func}_{val_col}" if val_col != "count" else "count"
        result_df.columns = [group_col, metric_col_name]
        result_df = result_df.sort_values(by=metric_col_name, ascending=plan.sort_ascending)
        result_df = result_df.head(plan.limit)

        rows = [sanitize_for_json(r) for r in result_df.to_dict(orient="records")]
        columns = list(result_df.columns)

        chart_data = [
            {"name": str(r[group_col]), "value": sanitize_for_json(r[metric_col_name])}
            for r in rows
        ]

        chart_config = plan.chart_recommendation or ChartConfig(
            chart_type="bar",
            x_axis="name",
            y_axis="value",
            title=f"{agg_func.title()} by {group_col.replace('_', ' ').title()}",
        )

        metrics = {
            "group_column": group_col,
            "aggregation": agg_func,
            "distinct_groups_analyzed": len(rows),
            "top_group": rows[0] if rows else None,
        }

        summary = f"Grouped {total_rows} records by '{group_col}' and computed '{agg_func}'. Returned top {len(rows)} categories."

        return QueryExecutionResult(
            table=QueryResultTable(columns=columns, rows=rows, total_rows=len(rows)),
            metrics=metrics,
            chart_data=chart_data,
            chart_config=chart_config,
            computation_summary=summary,
            row_count_analyzed=total_rows,
        )

    @staticmethod
    def _execute_aggregate(
        df: pd.DataFrame, plan: AnalyticalQueryPlan, total_rows: int
    ) -> QueryExecutionResult:
        target_col = plan.target_columns[0] if plan.target_columns else df.columns[0]
        agg_func = plan.aggregation_func or "count"

        num_series = pd.to_numeric(df[target_col], errors="coerce")
        metrics: Dict[str, Any] = {"column": target_col, "total_records": total_rows}

        if agg_func == "count":
            val = int(df[target_col].count())
        elif agg_func == "distinct_count":
            val = int(df[target_col].nunique())
        elif agg_func == "sum":
            val = float(num_series.sum())
        elif agg_func in ("mean", "avg"):
            val = float(num_series.mean())
        elif agg_func == "median":
            val = float(num_series.median())
        elif agg_func == "min":
            val = float(num_series.min())
        elif agg_func == "max":
            val = float(num_series.max())
        else:
            val = float(num_series.mean())

        metrics[f"{agg_func}_{target_col}"] = sanitize_for_json(val)

        # Include basic stats table
        stats_data = [
            {"metric": "Computed Value", "value": sanitize_for_json(val)},
            {"metric": "Non-Null Count", "value": int(df[target_col].count())},
            {"metric": "Null Count", "value": int(df[target_col].isna().sum())},
            {"metric": "Unique Count", "value": int(df[target_col].nunique())},
        ]
        if not num_series.dropna().empty:
            stats_data.extend([
                {"metric": "Mean", "value": sanitize_for_json(num_series.mean())},
                {"metric": "Min", "value": sanitize_for_json(num_series.min())},
                {"metric": "Max", "value": sanitize_for_json(num_series.max())},
            ])

        summary = f"Calculated {agg_func.upper()} for '{target_col}': {sanitize_for_json(val)} across {total_rows} records."

        return QueryExecutionResult(
            table=QueryResultTable(columns=["metric", "value"], rows=stats_data, total_rows=len(stats_data)),
            metrics=metrics,
            computation_summary=summary,
            row_count_analyzed=total_rows,
        )

    @staticmethod
    def _execute_sort_limit(
        df: pd.DataFrame, plan: AnalyticalQueryPlan, total_rows: int
    ) -> QueryExecutionResult:
        sort_col = plan.sort_by or (plan.target_columns[-1] if plan.target_columns else df.columns[0])

        # Attempt numeric conversion for numeric sort
        temp_df = df.copy()
        numeric_series = pd.to_numeric(temp_df[sort_col], errors="coerce")
        if numeric_series.notna().sum() > 0:
            temp_df["_sort_key"] = numeric_series
            sorted_df = temp_df.sort_values(by="_sort_key", ascending=plan.sort_ascending)
            sorted_df = sorted_df.drop(columns=["_sort_key"])
        else:
            sorted_df = temp_df.sort_values(by=sort_col, ascending=plan.sort_ascending)

        limited_df = sorted_df.head(plan.limit)
        columns = list(limited_df.columns)
        rows = [sanitize_for_json(r) for r in limited_df.to_dict(orient="records")]

        label_col = plan.target_columns[0] if len(plan.target_columns) > 1 else columns[0]
        chart_data = []
        if label_col != sort_col:
            for r in rows:
                chart_data.append({
                    "name": str(r.get(label_col, "")),
                    "value": sanitize_for_json(r.get(sort_col)),
                })

        chart_config = plan.chart_recommendation or ChartConfig(
            chart_type="bar",
            x_axis="name",
            y_axis="value",
            title=f"Top {len(rows)} by {sort_col.replace('_', ' ').title()}",
        )

        direction = "Ascending (Lowest)" if plan.sort_ascending else "Descending (Highest)"
        summary = f"Sorted {total_rows} records by '{sort_col}' in {direction} order. Displaying top {len(rows)} records."

        return QueryExecutionResult(
            table=QueryResultTable(columns=columns, rows=rows, total_rows=len(rows)),
            metrics={"sort_by": sort_col, "limit": len(rows)},
            chart_data=chart_data if chart_data else None,
            chart_config=chart_config if chart_data else None,
            computation_summary=summary,
            row_count_analyzed=total_rows,
        )

    @staticmethod
    def _execute_distribution(
        df: pd.DataFrame, plan: AnalyticalQueryPlan, total_rows: int
    ) -> QueryExecutionResult:
        target_col = plan.target_columns[0] if plan.target_columns else df.columns[0]
        num_series = pd.to_numeric(df[target_col], errors="coerce")

        if num_series.notna().sum() > len(df) * 0.5:
            # Numeric Histogram
            counts, bin_edges = np.histogram(num_series.dropna(), bins=min(10, total_rows))
            chart_data = []
            rows = []
            for i in range(len(counts)):
                label = f"{round(bin_edges[i], 1)} - {round(bin_edges[i+1], 1)}"
                chart_data.append({"name": label, "value": int(counts[i])})
                rows.append({"bin_range": label, "count": int(counts[i])})
            columns = ["bin_range", "count"]
            chart_type = "histogram"
        else:
            # Categorical Frequency
            val_counts = df[target_col].value_counts().head(plan.limit)
            chart_data = [{"name": str(k), "value": int(v)} for k, v in val_counts.items()]
            rows = [{"category": str(k), "count": int(v)} for k, v in val_counts.items()]
            columns = ["category", "count"]
            chart_type = "bar"

        summary = f"Calculated distribution for '{target_col}' with {len(rows)} distinct bins/categories."

        return QueryExecutionResult(
            table=QueryResultTable(columns=columns, rows=rows, total_rows=len(rows)),
            metrics={"column": target_col, "categories_count": len(rows)},
            chart_data=chart_data,
            chart_config=ChartConfig(
                chart_type=chart_type,
                x_axis="name",
                y_axis="value",
                title=f"Distribution of {target_col.replace('_', ' ').title()}",
            ),
            computation_summary=summary,
            row_count_analyzed=total_rows,
        )

    @staticmethod
    def _execute_outliers(
        df: pd.DataFrame, plan: AnalyticalQueryPlan, total_rows: int
    ) -> QueryExecutionResult:
        target_col = plan.target_columns[0] if plan.target_columns else df.columns[0]
        num_series = pd.to_numeric(df[target_col], errors="coerce").dropna()

        if num_series.empty or len(num_series) < 4:
            return QueryExecutionResult(
                table=QueryResultTable(columns=["message"], rows=[{"message": "Insufficient numeric values for outlier detection"}], total_rows=1),
                computation_summary=f"Column '{target_col}' has insufficient numeric data for statistical outlier detection.",
                row_count_analyzed=total_rows,
            )

        q1 = float(num_series.quantile(0.25))
        q3 = float(num_series.quantile(0.75))
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        temp_df = df.copy()
        temp_df["_num_val"] = pd.to_numeric(temp_df[target_col], errors="coerce")
        outlier_mask = (temp_df["_num_val"] < lower_bound) | (temp_df["_num_val"] > upper_bound)
        outlier_df = temp_df[outlier_mask].drop(columns=["_num_val"]).head(plan.limit)

        rows = [sanitize_for_json(r) for r in outlier_df.to_dict(orient="records")]
        columns = list(outlier_df.columns)

        metrics = {
            "column": target_col,
            "q1": round(q1, 4),
            "q3": round(q3, 4),
            "iqr": round(iqr, 4),
            "lower_bound": round(lower_bound, 4),
            "upper_bound": round(upper_bound, 4),
            "outlier_count": int(outlier_mask.sum()),
        }

        summary = (
            f"Detected {metrics['outlier_count']} outlier records in '{target_col}' outside the IQR range "
            f"[{metrics['lower_bound']} to {metrics['upper_bound']}]."
        )

        return QueryExecutionResult(
            table=QueryResultTable(columns=columns, rows=rows, total_rows=len(rows)),
            metrics=metrics,
            computation_summary=summary,
            row_count_analyzed=total_rows,
        )

    @staticmethod
    def _execute_correlation(
        df: pd.DataFrame, plan: AnalyticalQueryPlan, total_rows: int
    ) -> QueryExecutionResult:
        numeric_df = df.apply(pd.to_numeric, errors="coerce").dropna(how="all", axis=1)

        if numeric_df.shape[1] < 2:
            return QueryExecutionResult(
                table=QueryResultTable(columns=["message"], rows=[{"message": "Dataset requires at least 2 numeric columns for correlation analysis"}], total_rows=1),
                computation_summary="Dataset contains fewer than 2 numeric columns for correlation.",
                row_count_analyzed=total_rows,
            )

        corr_matrix = numeric_df.corr(method="pearson").round(4)
        corr_matrix_dict = {col: corr_matrix[col].to_dict() for col in corr_matrix.columns}

        # Find top correlation pairs
        pairs = []
        cols = list(corr_matrix.columns)
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                val = corr_matrix.iloc[i, j]
                if not math.isnan(val):
                    pairs.append({
                        "column_a": cols[i],
                        "column_b": cols[j],
                        "correlation": float(val),
                        "relationship": "Positive" if val > 0 else "Negative",
                        "strength": "Strong" if abs(val) >= 0.7 else "Moderate" if abs(val) >= 0.4 else "Weak",
                    })

        pairs.sort(key=lambda p: abs(p["correlation"]), reverse=True)

        rows = [sanitize_for_json(p) for p in pairs[:plan.limit]]
        columns = ["column_a", "column_b", "correlation", "relationship", "strength"]

        summary = f"Computed Pearson correlation matrix across {len(cols)} numeric columns. Identified {len(pairs)} correlation pairs."

        return QueryExecutionResult(
            table=QueryResultTable(columns=columns, rows=rows, total_rows=len(rows)),
            metrics={"top_pair": rows[0] if rows else None, "correlation_matrix": sanitize_for_json(corr_matrix_dict)},
            computation_summary=summary,
            row_count_analyzed=total_rows,
        )

    @staticmethod
    def _execute_missing_analysis(
        df: pd.DataFrame, plan: AnalyticalQueryPlan, total_rows: int
    ) -> QueryExecutionResult:
        missing_data = []
        for col in df.columns:
            null_count = int(df[col].isna().sum() + (df[col] == "").sum())
            pct = round((null_count / total_rows) * 100, 2) if total_rows > 0 else 0.0
            missing_data.append({
                "column": col,
                "missing_count": null_count,
                "present_count": total_rows - null_count,
                "missing_percentage": pct,
            })

        missing_data.sort(key=lambda x: x["missing_percentage"], reverse=True)
        rows = [sanitize_for_json(m) for m in missing_data]
        columns = ["column", "missing_count", "present_count", "missing_percentage"]

        chart_data = [{"name": m["column"], "value": m["missing_percentage"]} for m in rows]

        summary = f"Analyzed missing values across {len(df.columns)} columns. Found highest missing rate in '{rows[0]['column']}' ({rows[0]['missing_percentage']}%)."

        return QueryExecutionResult(
            table=QueryResultTable(columns=columns, rows=rows, total_rows=len(rows)),
            metrics={"total_columns": len(df.columns), "columns_with_missing": sum(1 for m in rows if m["missing_count"] > 0)},
            chart_data=chart_data,
            chart_config=ChartConfig(
                chart_type="bar",
                x_axis="name",
                y_axis="value",
                title="Missing Value Percentage by Column",
            ),
            computation_summary=summary,
            row_count_analyzed=total_rows,
        )

    @staticmethod
    def _execute_general_summary(
        df: pd.DataFrame, plan: AnalyticalQueryPlan, total_rows: int
    ) -> QueryExecutionResult:
        summary_rows = [
            {"metric": "Total Records", "value": total_rows},
            {"metric": "Total Columns", "value": len(df.columns)},
            {"metric": "Memory Usage (KB)", "value": round(df.memory_usage(deep=True).sum() / 1024, 2)},
        ]

        for col in df.columns[:5]:
            unique_count = int(df[col].nunique())
            summary_rows.append({
                "metric": f"Unique '{col}'",
                "value": unique_count,
            })

        summary = f"Analyzed dataset containing {total_rows} rows and {len(df.columns)} columns."

        return QueryExecutionResult(
            table=QueryResultTable(columns=["metric", "value"], rows=summary_rows, total_rows=len(summary_rows)),
            metrics={"total_rows": total_rows, "total_columns": len(df.columns)},
            computation_summary=summary,
            row_count_analyzed=total_rows,
        )
