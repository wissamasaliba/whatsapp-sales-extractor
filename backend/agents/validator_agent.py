"""
ValidatorAgent: cleans, normalises, and validates extracted sale records.
Uses Groq (qwen/qwen3-32b) to fix ambiguous or incomplete records.
"""

import json
from typing import List, Dict, Any, Tuple

from extractor import groq_client, MODEL

REQUIRED_FIELDS = ["timestamp", "sender", "product"]
NUMERIC_FIELDS = ["quantity", "unit_price", "total_price"]

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
        clean, needs_fix = self._split(sales)
        fixed = await self._fix_with_groq(needs_fix) if needs_fix else []
        return clean + fixed

    def _split(
        self, sales: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        clean, needs_fix = [], []
        for sale in sales:
            sale = self._coerce_numerics(sale)
            if self._is_valid(sale):
                clean.append(sale)
            else:
                needs_fix.append(sale)
        return clean, needs_fix

    def _coerce_numerics(self, sale: Dict[str, Any]) -> Dict[str, Any]:
        for field in NUMERIC_FIELDS:
            val = sale.get(field)
            if isinstance(val, str):
                try:
                    sale[field] = float(val.replace(",", ".").replace("R$", "").strip())
                except ValueError:
                    sale[field] = None
        return sale

    def _is_valid(self, sale: Dict[str, Any]) -> bool:
        return all(sale.get(f) for f in REQUIRED_FIELDS)

    async def _fix_with_groq(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
