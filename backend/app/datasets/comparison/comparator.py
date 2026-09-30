from typing import Any, Dict, List, Optional
import hashlib
import json
from collections import Counter


class DatasetComparator:
    """
    Compares two datasets owned by the authenticated user to highlight
    schema differences, record overlap, quality shifts, and new additions.
    """

    @classmethod
    def compare_datasets(
        cls,
        dataset_a_meta: Dict[str, Any],
        records_a: List[Dict[str, Any]],
        dataset_b_meta: Dict[str, Any],
        records_b: List[Dict[str, Any]],
        matching_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        count_a = len(records_a)
        count_b = len(records_b)

        # Extract schema fields
        cols_a = set()
        for r in records_a:
            data = r.get("record_data") or r.get("data") or r
            if isinstance(data, dict):
                cols_a.update(data.keys())

        cols_b = set()
        for r in records_b:
            data = r.get("record_data") or r.get("data") or r
            if isinstance(data, dict):
                cols_b.update(data.keys())

        common_cols = sorted(list(cols_a.intersection(cols_b)))
        a_only_cols = sorted(list(cols_a - cols_b))
        b_only_cols = sorted(list(cols_b - cols_a))

        # Record Matching (using matching_key or exact hash)
        def get_identifier(r: Dict[str, Any]) -> str:
            data = r.get("record_data") or r.get("data") or r
            if matching_key and isinstance(data, dict) and data.get(matching_key):
                return str(data[matching_key]).strip().lower()
            rec_hash = r.get("record_hash")
            if rec_hash:
                return rec_hash
            return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

        ids_a = set(get_identifier(r) for r in records_a)
        ids_b = set(get_identifier(r) for r in records_b)

        common_records_count = len(ids_a.intersection(ids_b))
        a_unique_records = len(ids_a - ids_b)
        b_new_records = len(ids_b - ids_a)

        # Quality Comparison
        qa = dataset_a_meta.get("quality_score", 0.0)
        qb = dataset_b_meta.get("quality_score", 0.0)
        quality_delta = round(qb - qa, 1)

        # Field Value Comparisons for up to 3 common fields
        field_comparisons = {}
        for col in common_cols[:4]:
            vals_a = [str((r.get("record_data") or {}).get(col)).strip() for r in records_a if (r.get("record_data") or {}).get(col)]
            vals_b = [str((r.get("record_data") or {}).get(col)).strip() for r in records_b if (r.get("record_data") or {}).get(col)]
            top_a = dict(Counter(vals_a).most_common(5))
            top_b = dict(Counter(vals_b).most_common(5))
            field_comparisons[col] = {
                "dataset_a_top": top_a,
                "dataset_b_top": top_b,
                "a_non_null": len(vals_a),
                "b_non_null": len(vals_b),
            }

        return {
            "dataset_a": {
                "id": str(dataset_a_meta.get("id")),
                "name": dataset_a_meta.get("name", "Dataset A"),
                "record_count": count_a,
                "quality_score": qa,
            },
            "dataset_b": {
                "id": str(dataset_b_meta.get("id")),
                "name": dataset_b_meta.get("name", "Dataset B"),
                "record_count": count_b,
                "quality_score": qb,
            },
            "comparison": {
                "record_count_delta": count_b - count_a,
                "quality_score_delta": quality_delta,
                "common_records_count": common_records_count,
                "dataset_a_unique_count": a_unique_records,
                "dataset_b_new_count": b_new_records,
                "matching_key_used": matching_key or "exact_record_hash",
            },
            "schema_diff": {
                "common_columns": common_cols,
                "dataset_a_only_columns": a_only_cols,
                "dataset_b_only_columns": b_only_cols,
                "similarity_score": round((2.0 * len(common_cols) / max(len(cols_a) + len(cols_b), 1)) * 100.0, 1),
            },
            "field_comparisons": field_comparisons,
        }
