import logging
from typing import List, Dict, Any, Tuple
import pandas as pd
from app.schemas.analysis import AnalyticalQueryPlan

logger = logging.getLogger(__name__)

ALLOWED_OPERATIONS = {
    "aggregate",
    "group_by",
    "sort_limit",
    "filter",
    "distribution",
    "outlier_detection",
    "correlation",
    "missing_analysis",
    "general_summary",
}

ALLOWED_AGG_FUNCTIONS = {
    "count",
    "sum",
    "mean",
    "median",
    "min",
    "max",
    "distinct_count",
}

ALLOWED_FILTER_OPERATORS = {
    "==",
    "!=",
    ">",
    "<",
    ">=",
    "<=",
    "contains",
    "is_null",
    "is_not_null",
}


class QueryValidator:
    @staticmethod
    def validate_plan(plan: AnalyticalQueryPlan, df: pd.DataFrame) -> Tuple[bool, str, AnalyticalQueryPlan]:
        """
        Validates the analytical query plan against the DataFrame schema and safety rules.
        Returns (is_valid, error_message, sanitized_plan).
        """
        if plan.operation not in ALLOWED_OPERATIONS:
            return False, f"Unsupported analytical operation: '{plan.operation}'", plan

        df_columns = set(df.columns)

        # 1. Sanitize & Validate target columns
        valid_targets = []
        for col in plan.target_columns:
            if col in df_columns:
                valid_targets.append(col)
            elif col.lower() in [c.lower() for c in df_columns]:
                # Case-insensitive match
                for real_col in df_columns:
                    if real_col.lower() == col.lower():
                        valid_targets.append(real_col)
                        break

        # Fallback if no target columns found
        if not valid_targets and len(df.columns) > 0:
            valid_targets = [df.columns[0]]

        plan.target_columns = valid_targets

        # 2. Validate group_by column
        if plan.group_by_column:
            if plan.group_by_column not in df_columns:
                matched = False
                for real_col in df_columns:
                    if real_col.lower() == plan.group_by_column.lower():
                        plan.group_by_column = real_col
                        matched = True
                        break
                if not matched:
                    plan.group_by_column = None

        # 3. Validate aggregation function
        if plan.aggregation_func:
            func = plan.aggregation_func.lower().replace("avg", "mean")
            if func not in ALLOWED_AGG_FUNCTIONS:
                plan.aggregation_func = "count"
            else:
                plan.aggregation_func = func

        # 4. Validate filter conditions
        valid_filters = []
        for f in plan.filters:
            if f.column in df_columns and f.operator in ALLOWED_FILTER_OPERATORS:
                valid_filters.append(f)
            else:
                for real_col in df_columns:
                    if real_col.lower() == f.column.lower() and f.operator in ALLOWED_FILTER_OPERATORS:
                        f.column = real_col
                        valid_filters.append(f)
                        break
        plan.filters = valid_filters

        # 5. Validate sort column
        if plan.sort_by and plan.sort_by not in df_columns:
            matched = False
            for real_col in df_columns:
                if real_col.lower() == plan.sort_by.lower():
                    plan.sort_by = real_col
                    matched = True
                    break
            if not matched:
                plan.sort_by = None

        # 6. Safety limit capping
        plan.limit = max(1, min(plan.limit, 500))

        # 7. Validate chart recommendation
        if plan.chart_recommendation:
            chart = plan.chart_recommendation
            if chart.x_axis not in df_columns:
                for real_col in df_columns:
                    if real_col.lower() == chart.x_axis.lower():
                        chart.x_axis = real_col
                        break
            if chart.y_axis and chart.y_axis not in df_columns:
                for real_col in df_columns:
                    if real_col.lower() == chart.y_axis.lower():
                        chart.y_axis = real_col
                        break

        return True, "", plan
