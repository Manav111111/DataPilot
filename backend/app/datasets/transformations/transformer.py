import copy
import hashlib
import json
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse


class DatasetTransformer:
    """
    Restricted, safe transformation engine using an allowlist of deterministic operations.
    Arbitrary user-provided code or SQL execution is strictly forbidden.
    """

    ALLOWED_OPERATIONS = [
        "rename_column",
        "derive_column",
        "filter_records",
    ]

    ALLOWED_EXPRESSION_TYPES = [
        "combine_text",
        "split_text",
        "extract_domain",
        "math_op",
        "value_map",
        "constant",
    ]

    @classmethod
    def compute_derived_value(
        cls,
        row_data: Dict[str, Any],
        expr_type: str,
        config: Dict[str, Any],
    ) -> Any:
        if expr_type == "combine_text":
            source_cols = config.get("source_columns", [])
            delimiter = config.get("delimiter", " ")
            parts = [str(row_data.get(c, "")).strip() for c in source_cols if row_data.get(c) is not None]
            parts = [p for p in parts if p]
            return delimiter.join(parts) if parts else None

        elif expr_type == "split_text":
            source_col = config.get("source_column")
            delimiter = config.get("delimiter", ",")
            part_index = int(config.get("part_index", 0))
            val = row_data.get(source_col)
            if val is not None:
                parts = str(val).split(delimiter)
                if 0 <= part_index < len(parts):
                    return parts[part_index].strip()
            return None

        elif expr_type == "extract_domain":
            source_col = config.get("source_column")
            val = row_data.get(source_col)
            if val and isinstance(val, str):
                sval = val.strip()
                if not sval.startswith("http://") and not sval.startswith("https://"):
                    sval = "https://" + sval
                try:
                    parsed = urlparse(sval)
                    domain = parsed.netloc.lower()
                    if domain.startswith("www."):
                        domain = domain[4:]
                    return domain if domain else None
                except Exception:
                    pass
            return None

        elif expr_type == "math_op":
            source_col = config.get("source_column")
            op = config.get("operator", "+")
            operand = float(config.get("operand", 0))
            val = row_data.get(source_col)
            if val is not None:
                try:
                    num_val = float(re.sub(r"[^\d.-]", "", str(val)))
                    if op == "+":
                        return round(num_val + operand, 2)
                    elif op == "-":
                        return round(num_val - operand, 2)
                    elif op == "*":
                        return round(num_val * operand, 2)
                    elif op == "/":
                        return round(num_val / operand, 2) if operand != 0 else None
                except Exception:
                    pass
            return None

        elif expr_type == "value_map":
            source_col = config.get("source_column")
            mapping = config.get("mapping", {})
            val = row_data.get(source_col)
            if val is not None:
                sval = str(val).strip()
                if sval in mapping:
                    return mapping[sval]
                for k, v in mapping.items():
                    if k.lower() == sval.lower():
                        return v
            return val

        elif expr_type == "constant":
            return config.get("constant_value")

        return None

    @classmethod
    def evaluate_filter_condition(
        cls,
        row_data: Dict[str, Any],
        config: Dict[str, Any],
    ) -> bool:
        field = config.get("filter_field")
        op = config.get("operator", "==")
        target_val = config.get("value")
        val = row_data.get(field)

        if op == "is_null":
            return val is None or str(val).strip() == "" or str(val).strip().lower() in ["null", "none"]
        elif op == "not_null":
            return val is not None and str(val).strip() != "" and str(val).strip().lower() not in ["null", "none"]

        if val is None:
            return False

        if op == "==":
            return str(val).strip().lower() == str(target_val).strip().lower()
        elif op == "!=":
            return str(val).strip().lower() != str(target_val).strip().lower()
        elif op == "contains":
            return str(target_val).strip().lower() in str(val).strip().lower()

        # Numeric comparisons
        try:
            num_val = float(re.sub(r"[^\d.-]", "", str(val)))
            num_target = float(target_val)
            if op == ">":
                return num_val > num_target
            elif op == ">=":
                return num_val >= num_target
            elif op == "<":
                return num_val < num_target
            elif op == "<=":
                return num_val <= num_target
        except Exception:
            pass

        return False

    @classmethod
    def preview_transformation(
        cls,
        records: List[Dict[str, Any]],
        operation_type: str,
        configuration: Dict[str, Any],
    ) -> Dict[str, Any]:
        if operation_type not in cls.ALLOWED_OPERATIONS:
            raise ValueError(f"Disallowed transformation operation: {operation_type}")

        samples = []
        affected_count = 0
        fields_affected = []
        warnings = []

        if operation_type == "rename_column":
            old_name = configuration.get("old_name")
            new_name = configuration.get("new_name")
            if not old_name or not new_name:
                raise ValueError("rename_column requires 'old_name' and 'new_name'")
            fields_affected = [old_name, new_name]

            for r in records:
                data = r.get("record_data") or r.get("data") or {}
                if old_name in data:
                    affected_count += 1
                    if len(samples) < 5:
                        samples.append({
                            "record_id": str(r.get("id")),
                            "original": {old_name: data[old_name]},
                            "transformed": {new_name: data[old_name]},
                        })

        elif operation_type == "derive_column":
            target_col = configuration.get("target_column")
            expr_type = configuration.get("expression_type")
            if not target_col or not expr_type:
                raise ValueError("derive_column requires 'target_column' and 'expression_type'")
            if expr_type not in cls.ALLOWED_EXPRESSION_TYPES:
                raise ValueError(f"Disallowed expression type: {expr_type}")

            fields_affected = [target_col]
            for r in records:
                data = r.get("record_data") or r.get("data") or {}
                derived_v = cls.compute_derived_value(data, expr_type, configuration)
                if derived_v is not None:
                    affected_count += 1
                if len(samples) < 5:
                    samples.append({
                        "record_id": str(r.get("id")),
                        "original": {k: data[k] for k in list(data.keys())[:3]},
                        "transformed": {target_col: derived_v},
                    })

        elif operation_type == "filter_records":
            action = configuration.get("action", "keep")  # keep or drop
            field = configuration.get("filter_field")
            fields_affected = [field] if field else []

            dropped_count = 0
            for r in records:
                data = r.get("record_data") or r.get("data") or {}
                matched = cls.evaluate_filter_condition(data, configuration)
                should_drop = (not matched) if action == "keep" else matched
                if should_drop:
                    dropped_count += 1
                    if len(samples) < 5:
                        samples.append({
                            "record_id": str(r.get("id")),
                            "original": data,
                            "action": "drop_record",
                        })

            affected_count = dropped_count
            if dropped_count > 0:
                warnings.append(f"This filter operation will permanently remove {dropped_count} records from the dataset.")

        return {
            "operation_type": operation_type,
            "configuration": configuration,
            "records_affected": affected_count,
            "fields_affected": fields_affected,
            "samples": samples,
            "warnings": warnings,
        }

    @classmethod
    def apply_transformation(
        cls,
        records: List[Dict[str, Any]],
        operation_type: str,
        configuration: Dict[str, Any],
    ) -> Dict[str, Any]:
        if operation_type not in cls.ALLOWED_OPERATIONS:
            raise ValueError(f"Disallowed transformation operation: {operation_type}")

        transformed_records = []
        deleted_record_ids = []
        affected_count = 0
        schema_updates = {}

        if operation_type == "rename_column":
            old_name = configuration.get("old_name")
            new_name = configuration.get("new_name")
            schema_updates = {"renamed_field": {"from": old_name, "to": new_name}}

            for r in records:
                rec_copy = copy.deepcopy(r)
                data = rec_copy.get("record_data") or rec_copy.get("data") or {}
                norm_data = rec_copy.get("normalized_data") or {}
                if old_name in data:
                    affected_count += 1
                    data[new_name] = data.pop(old_name)
                    if old_name in norm_data:
                        norm_data[new_name] = norm_data.pop(old_name)
                    rec_copy["record_data"] = data
                    rec_copy["normalized_data"] = norm_data
                    rec_copy["record_hash"] = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
                transformed_records.append(rec_copy)

        elif operation_type == "derive_column":
            target_col = configuration.get("target_column")
            expr_type = configuration.get("expression_type")
            schema_updates = {"added_field": {"name": target_col, "type": "string"}}

            for r in records:
                rec_copy = copy.deepcopy(r)
                data = rec_copy.get("record_data") or rec_copy.get("data") or {}
                norm_data = rec_copy.get("normalized_data") or {}
                derived_v = cls.compute_derived_value(data, expr_type, configuration)
                if derived_v is not None:
                    affected_count += 1
                data[target_col] = derived_v
                norm_data[target_col] = derived_v
                rec_copy["record_data"] = data
                rec_copy["normalized_data"] = norm_data
                rec_copy["record_hash"] = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
                transformed_records.append(rec_copy)

        elif operation_type == "filter_records":
            action = configuration.get("action", "keep")
            for r in records:
                rec_id = str(r.get("id"))
                data = r.get("record_data") or r.get("data") or {}
                matched = cls.evaluate_filter_condition(data, configuration)
                should_drop = (not matched) if action == "keep" else matched
                if should_drop:
                    deleted_record_ids.append(rec_id)
                else:
                    transformed_records.append(r)
            affected_count = len(deleted_record_ids)

        return {
            "transformed_records": transformed_records,
            "deleted_record_ids": deleted_record_ids,
            "records_affected": affected_count,
            "schema_updates": schema_updates,
        }
