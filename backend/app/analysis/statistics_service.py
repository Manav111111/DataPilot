import logging
import math
from typing import List, Dict, Any
import numpy as np
import pandas as pd
from app.schemas.analysis import (
    StatisticalAnalysisResponse,
    DescriptiveStat,
    CorrelationPair,
    OutlierReport,
)
from app.analysis.query_executor import sanitize_for_json

logger = logging.getLogger(__name__)


class StatisticsService:
    @staticmethod
    def calculate_statistics(
        df: pd.DataFrame, dataset_id: str, dataset_version: int
    ) -> StatisticalAnalysisResponse:
        """
        Computes descriptive statistics, correlation matrix, and outlier analysis.
        """
        row_count = len(df)
        descriptive_stats: List[DescriptiveStat] = []
        outliers_report: List[OutlierReport] = []

        # 1. Identify numeric columns
        numeric_cols = []
        for col in df.columns:
            s = pd.to_numeric(df[col], errors="coerce")
            if s.notna().sum() > 0:
                numeric_cols.append(col)

        # 2. Descriptive statistics & Outliers
        for col in numeric_cols:
            s = pd.to_numeric(df[col], errors="coerce").dropna()
            null_cnt = int(df[col].isna().sum() + (df[col] == "").sum())

            if not s.empty:
                cnt = int(len(s))
                mean_val = float(s.mean())
                std_val = float(s.std()) if len(s) > 1 else 0.0
                min_val = float(s.min())
                q25_val = float(s.quantile(0.25))
                med_val = float(s.median())
                q75_val = float(s.quantile(0.75))
                max_val = float(s.max())

                descriptive_stats.append(
                    DescriptiveStat(
                        column=col,
                        count=cnt,
                        mean=sanitize_for_json(mean_val),
                        std=sanitize_for_json(std_val),
                        min=sanitize_for_json(min_val),
                        q25=sanitize_for_json(q25_val),
                        median=sanitize_for_json(med_val),
                        q75=sanitize_for_json(q75_val),
                        max=sanitize_for_json(max_val),
                        null_count=null_cnt,
                    )
                )

                # Outliers using IQR
                iqr = q75_val - q25_val
                lower_b = q25_val - 1.5 * iqr
                upper_b = q75_val + 1.5 * iqr
                outlier_vals = s[(s < lower_b) | (s > upper_b)].tolist()

                outliers_report.append(
                    OutlierReport(
                        column=col,
                        lower_bound=sanitize_for_json(lower_b),
                        upper_bound=sanitize_for_json(upper_b),
                        outlier_count=len(outlier_vals),
                        sample_outlier_values=[sanitize_for_json(v) for v in outlier_vals[:5]],
                    )
                )

        # 3. Correlation Matrix & Top Pairs
        corr_matrix_dict: Dict[str, Dict[str, float]] = {}
        top_correlations: List[CorrelationPair] = []

        if len(numeric_cols) >= 2:
            num_df = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
            corr_df = num_df.corr(method="pearson").round(3)

            for c1 in corr_df.columns:
                corr_matrix_dict[c1] = {}
                for c2 in corr_df.columns:
                    val = corr_df.loc[c1, c2]
                    corr_matrix_dict[c1][c2] = None if math.isnan(val) else float(val)

            for i in range(len(numeric_cols)):
                for j in range(i + 1, len(numeric_cols)):
                    c1 = numeric_cols[i]
                    c2 = numeric_cols[j]
                    val = corr_df.loc[c1, c2]
                    if not math.isnan(val):
                        strength = (
                            "strong_positive"
                            if val >= 0.7
                            else "moderate_positive"
                            if val >= 0.4
                            else "strong_negative"
                            if val <= -0.7
                            else "moderate_negative"
                            if val <= -0.4
                            else "weak"
                        )
                        top_correlations.append(
                            CorrelationPair(
                                column_a=c1,
                                column_b=c2,
                                coefficient=float(val),
                                strength=strength,
                            )
                        )

            top_correlations.sort(key=lambda x: abs(x.coefficient), reverse=True)

        return StatisticalAnalysisResponse(
            dataset_id=dataset_id,
            dataset_version=dataset_version,
            record_count=row_count,
            descriptive_stats=descriptive_stats,
            correlation_matrix=corr_matrix_dict,
            top_correlations=top_correlations,
            outliers=outliers_report,
        )
