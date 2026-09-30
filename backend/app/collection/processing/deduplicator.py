import hashlib
import json
from typing import Dict, Any, List, Tuple, Set, Optional
from app.schemas.plan import CollectionPlanData, QualityRule
from app.collection.processing.validator import ValidatedRecord
from app.collection.extraction.structured_extractor import ExtractedFieldEvidence


class DeduplicationResult:
    def __init__(
        self,
        unique_records: List[ValidatedRecord],
        duplicate_count: int,
        merged_provenances: Dict[str, List[Tuple[str, ExtractedFieldEvidence]]],
    ):
        self.unique_records = unique_records
        self.duplicate_count = duplicate_count
        self.merged_provenances = merged_provenances  # record_hash -> list of (source_url, evidence)


class DeduplicationEngine:
    def __init__(self, plan_data: CollectionPlanData):
        self.plan_data = plan_data
        self.dedup_keys = self._determine_dedup_keys()

    def _determine_dedup_keys(self) -> List[str]:
        # Check plan quality rules first
        for rule in self.plan_data.quality_rules:
            if "dedup" in rule.rule_type.lower() and rule.target_fields:
                return [f.lower() for f in rule.target_fields]

        # Infer based on common naming patterns
        field_names = [f.name.lower() for f in self.plan_data.fields]
        keys = []
        for candidate in ["company_name", "company", "title", "job_title", "name", "website", "url", "domain"]:
            if candidate in field_names:
                keys.append(candidate)
            if len(keys) >= 2:
                break

        if not keys and field_names:
            keys = field_names[:2]
        return keys

    def compute_record_hash(self, record_data: Dict[str, Any]) -> str:
        """
        Computes deterministic SHA256 hash based on normalized deduplication key values.
        """
        key_values = []
        for k in self.dedup_keys:
            val = None
            for rk, rv in record_data.items():
                if rk.lower() == k.lower():
                    val = rv
                    break
            clean_str = str(val).strip().lower() if val is not None else ""
            key_values.append(clean_str)

        combined = "|".join(key_values)
        if not combined.replace("|", ""):
            # Fallback to entire record if dedup keys are empty
            combined = json.dumps(record_data, sort_keys=True)

        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    def process_records(
        self, records: List[ValidatedRecord]
    ) -> Tuple[List[ValidatedRecord], int, Dict[str, List[Tuple[str, ExtractedFieldEvidence]]]]:
        """
        Deduplicates a list of validated records, merges missing fields, and aggregates source evidence.
        Returns: (unique_records, duplicate_count, merged_provenances)
        """
        seen_hashes: Dict[str, ValidatedRecord] = {}
        merged_provenances: Dict[str, List[Tuple[str, ExtractedFieldEvidence]]] = {}
        duplicate_count = 0

        for rec in records:
            r_hash = self.compute_record_hash(rec.normalized_data)

            if r_hash in seen_hashes:
                duplicate_count += 1
                existing_rec = seen_hashes[r_hash]

                # Merge any missing fields into existing record
                for k, v in rec.normalized_data.items():
                    if existing_rec.normalized_data.get(k) is None and v is not None:
                        existing_rec.normalized_data[k] = v
                        existing_rec.record_data[k] = rec.record_data.get(k, v)

                # Collect new evidence from this duplicate source
                if r_hash not in merged_provenances:
                    merged_provenances[r_hash] = []

                for ev in rec.field_evidences:
                    merged_provenances[r_hash].append((rec.source_url, ev))
            else:
                seen_hashes[r_hash] = rec
                merged_provenances[r_hash] = [
                    (rec.source_url, ev) for ev in rec.field_evidences
                ]

        return list(seen_hashes.values()), duplicate_count, merged_provenances
