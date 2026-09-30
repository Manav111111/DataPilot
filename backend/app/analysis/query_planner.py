import logging
from typing import List, Dict, Any, Optional
from app.ai.providers import get_llm_provider
from app.schemas.analysis import AnalyticalQueryPlan, FilterCondition, ChartConfig

logger = logging.getLogger(__name__)


class QueryPlanner:
    def __init__(self):
        self.llm = get_llm_provider()

    async def plan_query(
        self,
        user_query: str,
        dataset_name: str,
        columns_info: List[Dict[str, Any]],
        row_count: int,
    ) -> AnalyticalQueryPlan:
        """
        Translates a natural-language question into a structured, validated AnalyticalQueryPlan.
        """
        columns_summary = []
        for col in columns_info:
            col_name = col.get("name", "")
            col_type = col.get("type", "string")
            samples = col.get("samples", [])
            columns_summary.append(
                f"- '{col_name}' ({col_type}) (examples: {samples[:3]})"
            )
        columns_text = "\n".join(columns_summary)

        system_instruction = (
            "You are an expert Data Intelligence Analyst. Your task is to convert a user's natural-language "
            "question about a dataset into a strict, safe AnalyticalQueryPlan JSON object.\n\n"
            "RULES:\n"
            "1. ONLY use columns that exist in the provided schema. Do not invent column names.\n"
            "2. Choose the best operation:\n"
            "   - 'aggregate': for summary metrics (sum, mean, median, min, max, count, distinct_count).\n"
            "   - 'group_by': for comparing categories (e.g. average salary by city, company count by industry).\n"
            "   - 'sort_limit': for top/bottom queries (e.g. top 5 highest priced products, 10 lowest funded startups).\n"
            "   - 'filter': for subsets matching specific conditions.\n"
            "   - 'distribution': for categorical frequency or numeric histogram.\n"
            "   - 'outlier_detection': for finding unusual/anomaly values.\n"
            "   - 'correlation': for relationships between two numeric columns.\n"
            "   - 'missing_analysis': for missing/null value questions.\n"
            "   - 'general_summary': for high-level overviews.\n"
            "3. Chart Recommendations:\n"
            "   - If the result is visualizable, recommend a chart_type ('bar', 'line', 'pie', 'area', 'histogram', 'scatter') "
            "with x_axis, y_axis, and descriptive title.\n"
            "4. Never output arbitrary code or SQL. Strictly populate the schema."
        )

        prompt = (
            f"Dataset Name: {dataset_name}\n"
            f"Total Records: {row_count}\n"
            f"Available Schema & Columns:\n{columns_text}\n\n"
            f"User Question: \"{user_query}\"\n\n"
            "Generate the optimal AnalyticalQueryPlan."
        )

        try:
            plan = await self.llm.generate_structured(
                prompt=prompt,
                response_schema=AnalyticalQueryPlan,
                system_instruction=system_instruction,
                temperature=0.1,
            )
            return plan
        except Exception as e:
            logger.warning(f"LLM query planning failed, falling back to heuristic planner: {e}")
            return self._heuristic_fallback_plan(user_query, columns_info, row_count)

    def _heuristic_fallback_plan(
        self, user_query: str, columns_info: List[Dict[str, Any]], row_count: int
    ) -> AnalyticalQueryPlan:
        """
        Heuristic rule-based fallback when LLM is in mock mode or unavailable.
        """
        q = user_query.lower()
        col_names = [c.get("name", "") for c in columns_info]
        num_cols = [c.get("name", "") for c in columns_info if c.get("type") in ("integer", "number", "float")]
        cat_cols = [c.get("name", "") for c in columns_info if c.get("type") in ("string", "category")]

        # Top / Highest / Most
        if any(w in q for w in ["top", "highest", "most", "expensive", "maximum", "best"]):
            target = num_cols[0] if num_cols else (col_names[0] if col_names else "id")
            label_col = cat_cols[0] if cat_cols else (col_names[0] if col_names else "id")
            return AnalyticalQueryPlan(
                operation="sort_limit",
                target_columns=[label_col, target] if label_col != target else [target],
                sort_by=target,
                sort_ascending=False,
                limit=10,
                chart_recommendation=ChartConfig(
                    chart_type="bar",
                    x_axis=label_col,
                    y_axis=target,
                    title=f"Top 10 Records by {target.replace('_', ' ').title()}",
                ),
                reasoning=f"Identified top ranking query sorting by {target}.",
            )

        # Average / Mean / Sum
        if any(w in q for w in ["average", "avg", "mean", "total", "sum"]):
            target = num_cols[0] if num_cols else (col_names[0] if col_names else "id")
            group = cat_cols[0] if cat_cols else None
            func = "sum" if "sum" in q or "total" in q else "mean"
            return AnalyticalQueryPlan(
                operation="group_by" if group else "aggregate",
                target_columns=[target],
                group_by_column=group,
                aggregation_func=func,
                limit=20,
                chart_recommendation=ChartConfig(
                    chart_type="bar",
                    x_axis=group or target,
                    y_axis=target if group else None,
                    title=f"{func.title()} {target.replace('_', ' ').title()}" + (f" by {group.title()}" if group else ""),
                ) if group else None,
                reasoning=f"Calculated {func} of {target}" + (f" grouped by {group}" if group else "") + ".",
            )

        # Outliers / Anomalies
        if any(w in q for w in ["outlier", "anomaly", "unusual", "abnormal"]):
            target = num_cols[0] if num_cols else (col_names[0] if col_names else "id")
            return AnalyticalQueryPlan(
                operation="outlier_detection",
                target_columns=[target],
                limit=25,
                reasoning=f"Identified outlier detection query for column {target}.",
            )

        # Correlation
        if any(w in q for w in ["correlation", "relationship", "relate", "vs", "versus"]):
            targets = num_cols[:2] if len(num_cols) >= 2 else col_names[:2]
            return AnalyticalQueryPlan(
                operation="correlation",
                target_columns=targets,
                chart_recommendation=ChartConfig(
                    chart_type="scatter",
                    x_axis=targets[0] if len(targets) > 0 else "x",
                    y_axis=targets[1] if len(targets) > 1 else "y",
                    title=f"Correlation between {targets[0]} and {targets[1] if len(targets)>1 else ''}",
                ) if len(targets) >= 2 else None,
                reasoning=f"Analyzed correlation between numerical columns.",
            )

        # Default: Summary overview
        first_col = cat_cols[0] if cat_cols else (col_names[0] if col_names else "id")
        return AnalyticalQueryPlan(
            operation="distribution" if cat_cols else "general_summary",
            target_columns=[first_col],
            group_by_column=first_col if cat_cols else None,
            aggregation_func="count",
            limit=15,
            chart_recommendation=ChartConfig(
                chart_type="bar" if cat_cols else "pie",
                x_axis=first_col,
                title=f"Distribution of {first_col.replace('_', ' ').title()}",
            ) if cat_cols else None,
            reasoning="Generated frequency overview of the dataset.",
        )
