from typing import Any, Dict, List
import re

class QualityScorer:
    """
    Computes transparent, deterministic data quality dimension scores (0-100)
    along with actionable rules, explanations, and improvement suggestions.
    """
    SCORING_VERSION = "v1.0"

    # Default dimension weights (sum to 1.0)
    WEIGHTS = {
        "completeness": 0.25,
        "validity": 0.25,
        "uniqueness": 0.20,
        "consistency": 0.15,
        "provenance": 0.15,
    }

    @classmethod
    def calculate_quality(
        cls,
        records: List[Dict[str, Any]],
        schema_fields: List[Dict[str, Any]],
        sources_count: int = 0,
        provenance_count: int = 0,
    ) -> Dict[str, Any]:
        total_records = len(records)
        if total_records == 0:
            return {
                "overall_score": 0.0,
                "dimension_scores": {
                    "completeness": 0.0,
                    "validity": 0.0,
                    "uniqueness": 0.0,
                    "consistency": 0.0,
                    "provenance": 0.0,
                },
                "dimensions": {
                    "completeness": {
                        "score": 0.0,
                        "affected_count": 0,
                        "rule": "Percentage of non-null values across all expected fields.",
                        "explanation": "Dataset is empty.",
                        "suggestions": ["Collect records to calculate data completeness."],
                    },
                    "validity": {
                        "score": 0.0,
                        "affected_count": 0,
                        "rule": "Percentage of records with valid status and conforming data types.",
                        "explanation": "Dataset is empty.",
                        "suggestions": [],
                    },
                    "uniqueness": {
                        "score": 100.0,
                        "affected_count": 0,
                        "rule": "Percentage of unique records with distinct entity identifiers.",
                        "explanation": "No duplicate records detected.",
                        "suggestions": [],
                    },
                    "consistency": {
                        "score": 0.0,
                        "affected_count": 0,
                        "rule": "Format uniformity across date, URL, email, and numeric columns.",
                        "explanation": "Dataset is empty.",
                        "suggestions": [],
                    },
                    "provenance": {
                        "score": 0.0,
                        "affected_count": 0,
                        "rule": "Percentage of records linked to verified source evidence.",
                        "explanation": "Dataset has no source evidence.",
                        "suggestions": ["Ensure collection sources are attached to records."],
                    },
                },
                "scoring_method_version": cls.SCORING_VERSION,
            }

        field_names = [f.get("name") for f in schema_fields if f.get("name")]
        if not field_names:
            # Infer from records
            all_keys = set()
            for r in records:
                data = r.get("record_data") or r.get("data") or r
                if isinstance(data, dict):
                    all_keys.update(data.keys())
            field_names = sorted(list(all_keys))

        required_fields = [f.get("name") for f in schema_fields if f.get("required")]

        # 1. Completeness Score
        total_cells = total_records * max(len(field_names), 1)
        populated_cells = 0
        records_missing_required = 0

        for r in records:
            data = r.get("record_data") or r.get("data") or r
            if not isinstance(data, dict):
                continue
            has_missing_req = False
            for fn in field_names:
                val = data.get(fn)
                if val is not None and str(val).strip() != "" and str(val).strip().lower() != "null":
                    populated_cells += 1
                elif fn in required_fields:
                    has_missing_req = True
            if has_missing_req:
                records_missing_required += 1

        completeness_ratio = populated_cells / max(total_cells, 1)
        completeness_score = round(completeness_ratio * 100.0, 1)

        completeness_sugg = []
        if records_missing_required > 0:
            completeness_sugg.append(f"{records_missing_required} records are missing required fields. Run cleaning to fill or filter them.")
        if completeness_score < 80.0:
            completeness_sugg.append("Use data cleaning tools to fill missing values with constants or defaults.")

        # 2. Validity Score
        valid_records = 0
        warning_records = 0
        invalid_records = 0

        for r in records:
            v_status = r.get("validation_status", "valid")
            if v_status == "valid":
                valid_records += 1
            elif v_status == "valid_with_warnings":
                warning_records += 1
            else:
                invalid_records += 1

        validity_score = round(((valid_records + (0.5 * warning_records)) / total_records) * 100.0, 1)
        validity_sugg = []
        if invalid_records > 0:
            validity_sugg.append(f"Inspect and fix {invalid_records} invalid records that failed field type validation.")
        if warning_records > 0:
            validity_sugg.append(f"{warning_records} records have warnings (e.g. non-standard formats or missing optional values).")

        # 3. Uniqueness Score
        seen_hashes = set()
        duplicate_count = 0
        for r in records:
            rec_hash = r.get("record_hash")
            if not rec_hash:
                data = r.get("record_data") or r.get("data") or r
                rec_hash = str(sorted(data.items())) if isinstance(data, dict) else str(data)
            if rec_hash in seen_hashes:
                duplicate_count += 1
            else:
                seen_hashes.add(rec_hash)

        unique_ratio = max(0.0, (total_records - duplicate_count) / total_records)
        uniqueness_score = round(unique_ratio * 100.0, 1)
        uniqueness_sugg = []
        if duplicate_count > 0:
            uniqueness_sugg.append(f"{duplicate_count} duplicate records detected. Resolve duplicate groups in the Duplicate Center.")

        # 4. Consistency Score
        # Check URL validity, date formats, whitespace issues
        inconsistent_cells = 0
        for r in records:
            data = r.get("record_data") or r.get("data") or r
            if not isinstance(data, dict):
                continue
            for fn, val in data.items():
                if val is None or val == "":
                    continue
                sval = str(val)
                # Whitespace inconsistency (leading/trailing whitespace or multiple spaces)
                if sval != sval.strip() or "  " in sval:
                    inconsistent_cells += 1
                # Check url fields
                elif "url" in fn.lower() or "website" in fn.lower() or "link" in fn.lower():
                    if not (sval.startswith("http://") or sval.startswith("https://")):
                        inconsistent_cells += 1

        consistency_ratio = max(0.0, 1.0 - (inconsistent_cells / max(total_cells, 1)))
        consistency_score = round(consistency_ratio * 100.0, 1)
        consistency_sugg = []
        if inconsistent_cells > 0:
            consistency_sugg.append(f"{inconsistent_cells} fields have untrimmed whitespace or non-standard URLs. Run Auto-Clean to standardize.")

        # 5. Provenance Score
        records_with_sources = 0
        for r in records:
            src_count = r.get("source_count", 0)
            if src_count and src_count > 0:
                records_with_sources += 1
            elif provenance_count > 0 and total_records > 0:
                # If aggregate provenance links exist
                records_with_sources = min(total_records, provenance_count)

        if total_records > 0 and records_with_sources == 0 and sources_count > 0:
            # Fallback if source records exist on dataset level
            records_with_sources = total_records

        provenance_score = round((records_with_sources / total_records) * 100.0, 1)
        provenance_sugg = []
        if provenance_score < 100.0:
            unbacked = total_records - records_with_sources
            provenance_sugg.append(f"{unbacked} records lack linked source URLs or evidence excerpts.")

        # Overall Weighted Score
        overall = (
            completeness_score * cls.WEIGHTS["completeness"]
            + validity_score * cls.WEIGHTS["validity"]
            + uniqueness_score * cls.WEIGHTS["uniqueness"]
            + consistency_score * cls.WEIGHTS["consistency"]
            + provenance_score * cls.WEIGHTS["provenance"]
        )
        overall_score = round(overall, 1)

        return {
            "overall_score": overall_score,
            "dimension_scores": {
                "completeness": completeness_score,
                "validity": validity_score,
                "uniqueness": uniqueness_score,
                "consistency": consistency_score,
                "provenance": provenance_score,
            },
            "dimensions": {
                "completeness": {
                    "score": completeness_score,
                    "affected_count": records_missing_required,
                    "rule": "Percentage of populated fields vs total expected fields.",
                    "explanation": f"{populated_cells} of {total_cells} total field cells populated ({completeness_score}%).",
                    "suggestions": completeness_sugg,
                },
                "validity": {
                    "score": validity_score,
                    "affected_count": invalid_records + warning_records,
                    "rule": "Records meeting type constraints and validation rules.",
                    "explanation": f"{valid_records} valid, {warning_records} with warnings, {invalid_records} invalid records.",
                    "suggestions": validity_sugg,
                },
                "uniqueness": {
                    "score": uniqueness_score,
                    "affected_count": duplicate_count,
                    "rule": "Percentage of distinct records without duplicates.",
                    "explanation": f"{duplicate_count} duplicate records found ({uniqueness_score}% unique).",
                    "suggestions": uniqueness_sugg,
                },
                "consistency": {
                    "score": consistency_score,
                    "affected_count": inconsistent_cells,
                    "rule": "Conformity to standard whitespace, URL schemes, and formatting.",
                    "explanation": f"{inconsistent_cells} formatting inconsistencies detected.",
                    "suggestions": consistency_sugg,
                },
                "provenance": {
                    "score": provenance_score,
                    "affected_count": total_records - records_with_sources,
                    "rule": "Traceability of records back to verified web sources and excerpts.",
                    "explanation": f"{records_with_sources} of {total_records} records backed by source evidence.",
                    "suggestions": provenance_sugg,
                },
            },
            "scoring_method_version": cls.SCORING_VERSION,
        }
