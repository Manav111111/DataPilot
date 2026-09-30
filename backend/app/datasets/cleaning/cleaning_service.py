import copy
import hashlib
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


class DatasetCleaningService:
    """
    Provides robust, auditable data cleaning operations with safe preview,
    loss warning detection, and explicit normalization transformations.
    """

    SUPPORTED_OPERATIONS = [
        "trim_whitespace",
        "normalize_blanks",
        "normalize_urls",
        "standardize_dates",
        "normalize_geo",
        "normalize_case",
        "convert_types",
        "remove_duplicates",
        "fill_missing_constant",
        "drop_missing_required",
        "map_values",
    ]

    GEO_MAP = {
        "bengaluru": "Bangalore",
        "blr": "Bangalore",
        "bombay": "Mumbai",
        "madras": "Chennai",
        "calcutta": "Kolkata",
        "nyc": "New York City",
        "ny": "New York",
        "sf": "San Francisco",
        "bay area": "San Francisco Bay Area",
        "usa": "United States",
        "us": "United States",
        "uk": "United Kingdom",
        "uae": "United Arab Emirates",
        "delhi ncr": "Delhi-NCR",
        "gurugram": "Gurgaon",
    }

    @classmethod
    def clean_cell_value(
        cls,
        field_name: str,
        value: Any,
        operation_type: str,
        config: Dict[str, Any],
    ) -> Tuple[Any, bool]:
        """
        Cleans a single cell value according to the operation.
        Returns: (new_value, was_changed)
        """
        if value is None:
            if operation_type == "fill_missing_constant":
                target_field = config.get("field_name")
                if not target_field or target_field == field_name:
                    fill_val = config.get("constant_value", "")
                    return fill_val, True
            return None, False

        target_field = config.get("field_name")
        target_fields = config.get("fields", [])
        if target_field and target_field != field_name:
            return value, False
        if target_fields and field_name not in target_fields:
            return value, False

        orig_val = value

        if operation_type == "trim_whitespace":
            if isinstance(value, str):
                cleaned = re.sub(r"\s+", " ", value).strip()
                return cleaned, cleaned != orig_val

        elif operation_type == "normalize_blanks":
            if isinstance(value, str):
                sval = value.strip()
                if sval == "" or sval.lower() in ["n/a", "na", "null", "none", "-", "--", "undefined"]:
                    return None, True
            return value, False

        elif operation_type == "normalize_urls":
            if isinstance(value, str) and ("url" in field_name.lower() or "website" in field_name.lower() or "link" in field_name.lower() or target_field == field_name):
                sval = value.strip()
                if sval:
                    if not sval.startswith("http://") and not sval.startswith("https://"):
                        sval = "https://" + sval
                    try:
                        parsed = urlparse(sval)
                        scheme = parsed.scheme.lower()
                        netloc = parsed.netloc.lower()
                        # Strip common tracking params
                        q_params = [
                            (k, v) for k, v in parse_qsl(parsed.query)
                            if not k.lower().startswith("utm_") and k.lower() not in ["ref", "fbclid", "gclid"]
                        ]
                        new_query = urlencode(q_params)
                        cleaned = urlunparse((scheme, netloc, parsed.path.rstrip("/"), parsed.params, new_query, ""))
                        return cleaned, cleaned != orig_val
                    except Exception:
                        pass

        elif operation_type == "standardize_dates":
            if isinstance(value, str) and ("date" in field_name.lower() or "time" in field_name.lower() or target_field == field_name):
                sval = value.strip()
                if sval:
                    # Common date formats
                    for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d", "%B %d, %Y", "%b %d, %Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
                        try:
                            dt = datetime.strptime(sval[:19], fmt if "%T" not in fmt else fmt)
                            cleaned = dt.strftime("%Y-%m-%d")
                            return cleaned, cleaned != orig_val
                        except Exception:
                            continue

        elif operation_type == "normalize_geo":
            if isinstance(value, str) and ("location" in field_name.lower() or "city" in field_name.lower() or "country" in field_name.lower() or target_field == field_name):
                sval = value.strip()
                lower_val = sval.lower()
                for k, v in cls.GEO_MAP.items():
                    if lower_val == k or lower_val.startswith(k + ",") or f" {k} " in f" {lower_val} ":
                        # Replace match
                        pattern = re.compile(re.escape(k), re.IGNORECASE)
                        cleaned = pattern.sub(v, sval)
                        return cleaned, cleaned != orig_val

        elif operation_type == "normalize_case":
            case_type = config.get("case_type", "title")  # lower, upper, title
            if isinstance(value, str):
                if case_type == "lower":
                    cleaned = value.lower()
                elif case_type == "upper":
                    cleaned = value.upper()
                else:
                    cleaned = value.title()
                return cleaned, cleaned != orig_val

        elif operation_type == "convert_types":
            target_type = config.get("target_type", "string")
            try:
                if target_type in ["number", "integer", "int"]:
                    if isinstance(value, (int, float)):
                        return int(value), int(value) != orig_val
                    cleaned_num = re.sub(r"[^\d.-]", "", str(value))
                    if cleaned_num:
                        return int(float(cleaned_num)), True
                elif target_type in ["float", "decimal"]:
                    cleaned_num = re.sub(r"[^\d.-]", "", str(value))
                    if cleaned_num:
                        return float(cleaned_num), True
                elif target_type in ["boolean", "bool"]:
                    sval = str(value).strip().lower()
                    return sval in ["true", "1", "yes", "t", "y"], True
                elif target_type == "string":
                    return str(value), not isinstance(orig_val, str)
            except Exception:
                pass

        elif operation_type == "fill_missing_constant":
            # Handled at start
            pass

        elif operation_type == "map_values":
            mapping = config.get("mapping", {})
            sval = str(value).strip()
            if sval in mapping:
                return mapping[sval], True
            if sval.lower() in {k.lower(): v for k, v in mapping.items()}:
                for k, v in mapping.items():
                    if k.lower() == sval.lower():
                        return v, True

        return value, False

    @classmethod
    def preview_clean(
        cls,
        records: List[Dict[str, Any]],
        operation_type: str,
        configuration: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Simulates cleaning operation across records and returns preview statistics and diffs.
        """
        if operation_type not in cls.SUPPORTED_OPERATIONS:
            raise ValueError(f"Unsupported cleaning operation: {operation_type}")

        affected_records = 0
        affected_fields_set = set()
        samples = []
        warnings = []
        potential_info_loss = False

        if operation_type == "remove_duplicates":
            seen_hashes = set()
            dup_ids = []
            for r in records:
                rec_id = str(r.get("id"))
                rec_hash = r.get("record_hash")
                if not rec_hash:
                    data = r.get("record_data") or r.get("data") or r
                    rec_hash = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
                if rec_hash in seen_hashes:
                    dup_ids.append(rec_id)
                    if len(samples) < 5:
                        samples.append({
                            "record_id": rec_id,
                            "original": r.get("record_data") or r.get("data") or {},
                            "cleaned": None,
                            "action": "delete_duplicate",
                        })
                else:
                    seen_hashes.add(rec_hash)

            affected_records = len(dup_ids)
            potential_info_loss = affected_records > 0
            if affected_records > 0:
                warnings.append(f"This operation will permanently remove {affected_records} exact duplicate records.")

            return {
                "operation_type": operation_type,
                "configuration": configuration,
                "records_affected": affected_records,
                "fields_affected": ["_record"],
                "samples": samples,
                "potential_info_loss": potential_info_loss,
                "warnings": warnings,
            }

        elif operation_type == "drop_missing_required":
            required_fields = configuration.get("required_fields", [])
            if not required_fields:
                req_f = configuration.get("field_name")
                if req_f:
                    required_fields = [req_f]

            dropped_ids = []
            for r in records:
                rec_id = str(r.get("id"))
                data = r.get("record_data") or r.get("data") or r
                if not isinstance(data, dict):
                    continue
                is_missing = False
                for rf in required_fields:
                    val = data.get(rf)
                    if val is None or str(val).strip() == "" or str(val).strip().lower() in ["null", "none", "n/a"]:
                        is_missing = True
                        break
                if is_missing:
                    dropped_ids.append(rec_id)
                    if len(samples) < 5:
                        samples.append({
                            "record_id": rec_id,
                            "original": data,
                            "cleaned": None,
                            "action": "drop_missing_required",
                        })

            affected_records = len(dropped_ids)
            potential_info_loss = affected_records > 0
            if affected_records > 0:
                warnings.append(f"This operation will drop {affected_records} records missing required values in {required_fields}.")

            return {
                "operation_type": operation_type,
                "configuration": configuration,
                "records_affected": affected_records,
                "fields_affected": required_fields,
                "samples": samples,
                "potential_info_loss": potential_info_loss,
                "warnings": warnings,
            }

        # Cell-level operations
        for r in records:
            rec_id = str(r.get("id"))
            data = r.get("record_data") or r.get("data") or r
            if not isinstance(data, dict):
                continue

            orig_dict = {}
            cleaned_dict = {}
            row_changed = False

            for k, v in data.items():
                new_v, changed = cls.clean_cell_value(k, v, operation_type, configuration)
                if changed:
                    row_changed = True
                    affected_fields_set.add(k)
                    orig_dict[k] = v
                    cleaned_dict[k] = new_v

            if row_changed:
                affected_records += 1
                if len(samples) < 5:
                    samples.append({
                        "record_id": rec_id,
                        "original": orig_dict,
                        "cleaned": cleaned_dict,
                        "action": "update",
                    })

        if operation_type in ["normalize_case", "convert_types", "map_values"]:
            potential_info_loss = True
            warnings.append("Original raw string casing or formatting will be converted.")

        return {
            "operation_type": operation_type,
            "configuration": configuration,
            "records_affected": affected_records,
            "fields_affected": sorted(list(affected_fields_set)),
            "samples": samples,
            "potential_info_loss": potential_info_loss,
            "warnings": warnings,
        }

    @classmethod
    def apply_clean(
        cls,
        records: List[Dict[str, Any]],
        operation_type: str,
        configuration: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Executes cleaning operation on records.
        Returns:
            - cleaned_records: modified list of record dicts
            - deleted_record_ids: list of dropped record IDs
            - records_affected: integer count
        """
        if operation_type not in cls.SUPPORTED_OPERATIONS:
            raise ValueError(f"Unsupported cleaning operation: {operation_type}")

        deleted_record_ids = []
        cleaned_records = []
        modified_count = 0

        if operation_type == "remove_duplicates":
            seen_hashes = set()
            for r in records:
                rec_id = str(r.get("id"))
                rec_hash = r.get("record_hash")
                if not rec_hash:
                    data = r.get("record_data") or r.get("data") or r
                    rec_hash = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
                if rec_hash in seen_hashes:
                    deleted_record_ids.append(rec_id)
                else:
                    seen_hashes.add(rec_hash)
                    cleaned_records.append(r)
            return {
                "cleaned_records": cleaned_records,
                "deleted_record_ids": deleted_record_ids,
                "records_affected": len(deleted_record_ids),
            }

        elif operation_type == "drop_missing_required":
            required_fields = configuration.get("required_fields", [])
            if not required_fields:
                req_f = configuration.get("field_name")
                if req_f:
                    required_fields = [req_f]

            for r in records:
                rec_id = str(r.get("id"))
                data = r.get("record_data") or r.get("data") or r
                if not isinstance(data, dict):
                    cleaned_records.append(r)
                    continue
                is_missing = False
                for rf in required_fields:
                    val = data.get(rf)
                    if val is None or str(val).strip() == "" or str(val).strip().lower() in ["null", "none", "n/a"]:
                        is_missing = True
                        break
                if is_missing:
                    deleted_record_ids.append(rec_id)
                else:
                    cleaned_records.append(r)
            return {
                "cleaned_records": cleaned_records,
                "deleted_record_ids": deleted_record_ids,
                "records_affected": len(deleted_record_ids),
            }

        # Cell-level operations
        for r in records:
            rec_copy = copy.deepcopy(r)
            data = rec_copy.get("record_data") or rec_copy.get("data") or {}
            norm_data = rec_copy.get("normalized_data") or {}
            row_changed = False

            for k, v in list(data.items()):
                new_v, changed = cls.clean_cell_value(k, v, operation_type, configuration)
                if changed:
                    row_changed = True
                    data[k] = new_v
                    if k in norm_data or norm_data:
                        norm_data[k] = new_v

            if row_changed:
                modified_count += 1
                rec_copy["record_data"] = data
                rec_copy["normalized_data"] = norm_data
                # Recalculate hash
                rec_copy["record_hash"] = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

            cleaned_records.append(rec_copy)

        return {
            "cleaned_records": cleaned_records,
            "deleted_record_ids": deleted_record_ids,
            "records_affected": modified_count,
        }
