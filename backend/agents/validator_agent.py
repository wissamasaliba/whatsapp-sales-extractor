"""
ValidatorAgent: cleans, normalises, and validates extracted sale records.
Uses Groq (qwen/qwen3-32b) to fix ambiguous or incomplete records.
"""

import json
import re
from typing import List, Dict, Any, Tuple

from extractor import groq_client, MODEL

REQUIRED_FIELDS = ["timestamp", "sender", "product"]
NUMERIC_FIELDS = ["quantity", "unit_price", "total_price"]

# Patterns that indicate a WhatsApp media-only message with no extractable text
MEDIA_PATTERNS = re.compile(
    r"<media omitted>|image omitted|video omitted|audio omitted|"
    r"sticker omitted|gif omitted|media omitted",
    re.IGNORECASE,
)

FIX_PROMPT = """
You are a data quality specialist. The following JSON objects are sale records that
may have missing or inconsistent fields. For each record:
1. Infer missing numeric fields if they can be derived (e.g. total = quantity × unit_price).
2. Standardise currency to a 3-letter ISO code (BRL, USD, EUR, etc.) where possible.
3. Keep the product description concise but descriptive.
4. Do not invent data — leave a field null if it truly cannot be inferred.

Return a JSON array of corrected records. Return ONLY the JSON array.
"""


class ValidatorAgent:
    async def run(self, sales: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate and normalise a list of raw sale records.

        Splits records into already-valid ones and those needing LLM repair,
        then merges the results.

        Args:
            sales: Raw sale dicts from ExtractorAgent.

        Returns:
            Combined list of clean and LLM-repaired sale dicts that pass
            all required-field checks.
        """
        clean, needs_fix = self._split(sales)
        fixed = await self._fix_with_groq(needs_fix) if needs_fix else []
        return clean + fixed

    def _split(
        self, sales: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Partition sales into clean records and those requiring LLM repair.

        Media-only placeholders are silently discarded here. Numeric fields
        are coerced before the validity check so that string prices from the
        LLM do not cause false negatives.

        Args:
            sales: Raw sale dicts to partition.

        Returns:
            Tuple of (clean_records, records_needing_fix).
        """
        clean, needs_fix = [], []
        for sale in sales:
            # Silently drop media-only placeholders — nothing to extract
            if self._is_media_only(sale):
                continue
            sale = self._coerce_numerics(sale)
            if self._is_valid(sale):
                clean.append(sale)
            else:
                # Only reaches here when there IS a real product but fields are incomplete
                needs_fix.append(sale)
        return clean, needs_fix

    def _is_media_only(self, sale: Dict[str, Any]) -> bool:
        """
        Return True when the record originates from a media placeholder message
        and contains no extractable sales data.
        """
        product = (sale.get("product") or "").strip()
        if product and MEDIA_PATTERNS.search(product):
            return True
        # No product AND no numeric data → nothing to work with
        has_product = bool(product)
        has_any_numeric = any(sale.get(f) for f in NUMERIC_FIELDS)
        return not has_product and not has_any_numeric

    def _coerce_numerics(self, sale: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert any string-typed numeric fields to float in-place.

        Handles comma-as-decimal and currency prefix stripping (e.g. "R$12,50").
        Sets the field to None if conversion fails.

        Args:
            sale: Sale dict to mutate.

        Returns:
            The same dict with numeric fields coerced.
        """
        for field in NUMERIC_FIELDS:
            val = sale.get(field)
            if isinstance(val, str):
                try:
                    sale[field] = float(val.replace(",", ".").replace("R$", "").strip())
                except ValueError:
                    sale[field] = None
        return sale

    def _is_valid(self, sale: Dict[str, Any]) -> bool:
        """
        Return True if all required fields (timestamp, sender, product) are present and non-empty.

        Args:
            sale: Sale dict to check.

        Returns:
            True if the record is considered valid, False otherwise.
        """
        return all(sale.get(f) for f in REQUIRED_FIELDS)

    async def _fix_with_groq(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Send incomplete sale records to the Groq LLM for best-effort repair.

        The LLM is prompted to infer missing numeric fields, standardise currency
        codes, and keep descriptions concise without inventing data.

        Args:
            records: List of sale dicts that failed local validation.

        Returns:
            List of repaired sale dicts that pass the validity check.
            Returns an empty list if the LLM response cannot be parsed.
        """
        payload = json.dumps(records, ensure_ascii=False)
        response = groq_client.chat.completions.create(
            model=MODEL,
            max_tokens=4096,
            reasoning_effort="none",
            messages=[
                {"role": "system", "content": FIX_PROMPT},
                {"role": "user", "content": payload},
            ],
        )
        try:
            fixed = json.loads(response.choices[0].message.content)
            return [s for s in fixed if self._is_valid(s)]
        except json.JSONDecodeError:
            return []
