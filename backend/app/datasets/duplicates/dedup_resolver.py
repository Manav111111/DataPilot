import copy
import hashlib
import json
import re
from typing import Any, Dict, List, Optional
from collections import defaultdict


class DuplicateResolver:
    """
    Identifies duplicate record clusters based on exact hashes, canonical URLs,
    and composite key matching, supporting side-by-side review and non-destructive merges.
    """

    @classmethod
    def find_duplicate_groups(
        cls,
        records: List[Dict[str, Any]],
        key_fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Groups records by exact hash, canonical URLs, or composite key fields.
        """
        groups = []
        seen_record_ids = set()

        # 1. Exact Hash Matching
        hash_to_records = defaultdict(list)
        for r in records:
            rec_hash = r.get("record_hash")
            if not rec_hash:
                data = r.get("record_data") or r.get("data") or r
                rec_hash = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
            hash_to_records[rec_hash].append(r)

        for h, rec_list in hash_to_records.items():
            if len(rec_list) > 1:
                group_rec_ids = [str(r.get("id")) for r in rec_list]
                seen_record_ids.update(group_rec_ids)
                groups.append({
                    "group_id": f"hash_{h[:12]}",
                    "rule_type": "exact_hash",
                    "match_field": "_record_hash",
                    "match_value": h[:12],
                    "confidence": 1.0,
                    "record_count": len(rec_list),
                    "records": rec_list,
                })

        # 2. Canonical URL / Identifier Matching (for records not yet in exact groups)
        url_fields = ["job_url", "url", "website", "company_website", "canonical_url", "source_url"]
        for uf in url_fields:
            url_to_records = defaultdict(list)
            for r in records:
                rec_id = str(r.get("id"))
                if rec_id in seen_record_ids:
                    continue
                data = r.get("record_data") or r.get("data") or {}
                val = data.get(uf)
                if val and isinstance(val, str) and len(val.strip()) > 8:
                    clean_url = val.strip().lower().rstrip("/")
                    url_to_records[clean_url].append(r)

            for u, rec_list in url_to_records.items():
                if len(rec_list) > 1:
                    group_rec_ids = [str(r.get("id")) for r in rec_list]
                    seen_record_ids.update(group_rec_ids)
                    groups.append({
                        "group_id": f"url_{hashlib.md5(u.encode()).hexdigest()[:10]}",
                        "rule_type": "canonical_url",
                        "match_field": uf,
                        "match_value": u,
                        "confidence": 0.95,
                        "record_count": len(rec_list),
                        "records": rec_list,
                    })

        # 3. Composite Key Matching (e.g. company + job_title)
        composite_keys = key_fields or [
            ["company_name", "job_title"],
            ["company", "title"],
            ["name", "location"],
        ]

        for ck_tuple in composite_keys:
            if isinstance(ck_tuple, str):
                ck_list = [ck_tuple]
            else:
                ck_list = ck_tuple

            ck_to_records = defaultdict(list)
            for r in records:
                rec_id = str(r.get("id"))
                if rec_id in seen_record_ids:
                    continue
                data = r.get("record_data") or r.get("data") or {}
                vals = [str(data.get(k, "")).strip().lower() for k in ck_list if data.get(k)]
                if len(vals) == len(ck_list) and all(len(v) > 2 for v in vals):
                    comp_key = "::".join(vals)
                    ck_to_records[comp_key].append(r)

            for comp_k, rec_list in ck_to_records.items():
                if len(rec_list) > 1:
                    group_rec_ids = [str(r.get("id")) for r in rec_list]
                    seen_record_ids.update(group_rec_ids)
                    groups.append({
                        "group_id": f"comp_{hashlib.md5(comp_k.encode()).hexdigest()[:10]}",
                        "rule_type": "composite_key",
                        "match_field": "+".join(ck_list),
                        "match_value": comp_k,
                        "confidence": 0.90,
                        "record_count": len(rec_list),
                        "records": rec_list,
                    })

        return groups

    @classmethod
    def prepare_merged_record(
        cls,
        retained_record: Dict[str, Any],
        merged_records: List[Dict[str, Any]],
        field_overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Combines data from merged records into the retained record, filling missing values
        and applying explicit user field overrides.
        """
        res_data = copy.deepcopy(retained_record.get("record_data") or retained_record.get("data") or {})

        # Fill missing values from merged records
        for mr in merged_records:
            m_data = mr.get("record_data") or mr.get("data") or {}
            for k, v in m_data.items():
                if (k not in res_data or res_data[k] is None or res_data[k] == "") and v is not None:
                    res_data[k] = v

        # Apply user overrides
        if field_overrides:
            for k, v in field_overrides.items():
                res_data[k] = v

        new_hash = hashlib.sha256(json.dumps(res_data, sort_keys=True).encode()).hexdigest()
        updated_rec = copy.deepcopy(retained_record)
        updated_rec["record_data"] = res_data
        updated_rec["normalized_data"] = copy.deepcopy(res_data)
        updated_rec["record_hash"] = new_hash
        updated_rec["source_count"] = (retained_record.get("source_count") or 1) + sum(
            mr.get("source_count") or 1 for mr in merged_records
        )

        return updated_rec
