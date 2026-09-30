import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from pydantic import BaseModel, Field
from app.schemas.plan import FieldDefinition, CollectionPlanData
from app.collection.extraction.structured_extractor import RawExtractedRecord, ExtractedFieldEvidence


class ValidationError(BaseModel):
    field_name: str
    error_type: str
    message: str
    severity: str = "error"  # "error" or "warning"


class ValidatedRecord(BaseModel):
    record_data: Dict[str, Any]
    normalized_data: Dict[str, Any]
    validation_status: str  # "valid", "valid_with_warnings", "invalid"
    validation_errors: List[ValidationError] = Field(default_factory=list)
    field_evidences: List[ExtractedFieldEvidence] = Field(default_factory=list)
    source_url: str
    page_title: Optional[str] = None
    domain: Optional[str] = None


class RecordValidator:
    def __init__(self, plan_data: CollectionPlanData):
        self.plan_data = plan_data
        self.fields_map: Dict[str, FieldDefinition] = {
            f.name.lower(): f for f in plan_data.fields
        }

    def validate_and_normalize(self, raw_record: RawExtractedRecord) -> ValidatedRecord:
        record_data = raw_record.record_data
        normalized_data: Dict[str, Any] = {}
        errors: List[ValidationError] = []

        for field_def in self.plan_data.fields:
            fname = field_def.name
            raw_val = record_data.get(fname)
            if raw_val is None:
                # Check case insensitive
                for k, v in record_data.items():
                    if k.lower() == fname.lower():
                        raw_val = v
                        break

            # 1. Required Check
            if raw_val is None or (isinstance(raw_val, str) and not raw_val.strip()):
                if field_def.required:
                    errors.append(
                        ValidationError(
                            field_name=fname,
                            error_type="missing_required_field",
                            message=f"Required field '{fname}' is missing or empty",
                            severity="error",
                        )
                    )
                normalized_data[fname] = None
                continue

            # 2. Type validation and normalization
            norm_val, field_errors = self._normalize_and_validate_type(fname, raw_val, field_def.type)
            normalized_data[fname] = norm_val
            errors.extend(field_errors)

        # Classify record status
        has_critical_error = any(e.severity == "error" for e in errors)
        has_warnings = any(e.severity == "warning" for e in errors)

        if has_critical_error:
            status = "invalid"
        elif has_warnings:
            status = "valid_with_warnings"
        else:
            status = "valid"

        return ValidatedRecord(
            record_data=record_data,
            normalized_data=normalized_data,
            validation_status=status,
            validation_errors=errors,
            field_evidences=raw_record.field_evidences,
            source_url=raw_record.source_url,
            page_title=raw_record.page_title,
            domain=raw_record.domain,
        )

    def _normalize_and_validate_type(
        self, field_name: str, value: Any, field_type: str
    ) -> Tuple[Any, List[ValidationError]]:
        errors: List[ValidationError] = []
        ftype = field_type.lower()

        # Normalize string whitespace
        if isinstance(value, str):
            value = " ".join(value.split())

        if ftype in ("string", "text"):
            return str(value), errors

        elif ftype in ("number", "integer", "float"):
            if isinstance(value, (int, float)):
                return value, errors
            if isinstance(value, str):
                # Clean numeric symbols like commas, currency symbols
                clean_num_str = re.sub(r"[^\d.-]", "", value)
                try:
                    if "." in clean_num_str:
                        return float(clean_num_str), errors
                    return int(clean_num_str), errors
                except ValueError:
                    errors.append(
                        ValidationError(
                            field_name=field_name,
                            error_type="invalid_number",
                            message=f"Value '{value}' could not be converted to a valid number",
                            severity="warning",
                        )
                    )
                    return value, errors
            return value, errors

        elif ftype == "url":
            if not isinstance(value, str):
                errors.append(
                    ValidationError(
                        field_name=field_name,
                        error_type="invalid_url",
                        message=f"Expected URL string, got {type(value).__name__}",
                        severity="error",
                    )
                )
                return value, errors

            # Normalize URL (clean tracking params, ensure scheme)
            norm_url = value.strip()
            if not norm_url.startswith(("http://", "https://")):
                norm_url = "https://" + norm_url

            try:
                parsed = urlparse(norm_url)
                if not parsed.netloc:
                    errors.append(
                        ValidationError(
                            field_name=field_name,
                            error_type="invalid_url",
                            message=f"Malformed URL '{value}'",
                            severity="warning",
                        )
                    )
                    return value, errors

                # Strip UTM tracking query parameters
                qs = parse_qs(parsed.query)
                clean_qs = {k: v for k, v in qs.items() if not k.lower().startswith("utm_")}
                clean_query = urlencode(clean_qs, doseq=True)

                normalized_url = urlunparse(
                    (
                        parsed.scheme.lower(),
                        parsed.netloc.lower(),
                        parsed.path.rstrip("/") if parsed.path != "/" else "/",
                        parsed.params,
                        clean_query,
                        "",
                    )
                )
                return normalized_url, errors
            except Exception:
                errors.append(
                    ValidationError(
                        field_name=field_name,
                        error_type="invalid_url",
                        message=f"Failed to parse URL '{value}'",
                        severity="warning",
                    )
                )
                return value, errors

        elif ftype == "email":
            email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
            if isinstance(value, str) and re.match(email_pattern, value.strip()):
                return value.strip().lower(), errors
            errors.append(
                ValidationError(
                    field_name=field_name,
                    error_type="invalid_email",
                    message=f"Invalid email format: '{value}'",
                    severity="warning",
                )
            )
            return value, errors

        elif ftype == "boolean":
            if isinstance(value, bool):
                return value, errors
            if isinstance(value, str):
                v_lower = value.lower()
                if v_lower in ("true", "yes", "1", "y", "t"):
                    return True, errors
                if v_lower in ("false", "no", "0", "n", "f"):
                    return False, errors
            return bool(value), errors

        elif ftype == "array":
            if isinstance(value, list):
                return value, errors
            if isinstance(value, str):
                items = [i.strip() for i in value.split(",") if i.strip()]
                return items, errors
            return [value], errors

        return value, errors
