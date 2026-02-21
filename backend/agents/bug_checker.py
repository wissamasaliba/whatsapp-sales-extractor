"""
BugChecker: scans the full set of validated sales for anomalies,
duplicates, and logical inconsistencies.
"""

import json
import re
from typing import List, Dict, Any, Tuple

from extractor import groq_client, MODEL

# Same media-placeholder pattern used by ValidatorAgent
MEDIA_PATTERNS = re.compile(
    r"<media omitted>|image omitted|video omitted|audio omitted|"
    r"sticker omitted|gif omitted|media omitted",
    re.IGNORECASE,
)

AUDIT_PROMPT = """
You are a data auditor reviewing a list of extracted sales records for a business.
Identify any of the following issues:
- Duplicate records (same sender, product, timestamp)
- Prices that are suspiciously high or low compared to other records for the same product
- Quantity/price arithmetic inconsistencies (unit_price × quantity ≠ total_price)
- Records with a real product name but missing both price and quantity

Do NOT flag records whose product is a media placeholder such as
"<Media omitted>", "image omitted", "video omitted", etc. — those should be silently ignored.

Return a JSON object with two keys:
- "sales": the cleaned list (remove confirmed duplicates, fix arithmetic if possible)
- "errors": a list of objects, each with "record" (the problematic sale) and "reason" (string)

Return ONLY the JSON object.
"""


class BugChecker:
    async def run(self, sales: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Fast local checks first
        sales, local_errors = self._local_checks(sales)

        if not sales:
            return {"sales": [], "errors": local_errors}

        # Deep audit via Groq
        payload = json.dumps(sales, ensure_ascii=False)
        response = groq_client.chat.completions.create(
            model=MODEL,
            max_tokens=4096,
            reasoning_effort="none",
            messages=[
                {"role": "system", "content": AUDIT_PROMPT},
                {"role": "user", "content": payload},
            ],
        )

        try:
            result = json.loads(response.choices[0].message.content)
            result["errors"] = local_errors + result.get("errors", [])
            return result
        except json.JSONDecodeError:
            return {
                "sales": sales,
                "errors": local_errors + [{"reason": "BugChecker LLM response could not be parsed."}],
            }

    def _is_media_only(self, sale: Dict[str, Any]) -> bool:
        product = (sale.get("product") or "").strip()
        if product and MEDIA_PATTERNS.search(product):
            return True
        has_product = bool(product)
        has_any_numeric = any(sale.get(f) for f in ["quantity", "unit_price", "total_price"])
        return not has_product and not has_any_numeric

    def _local_checks(
        self, sales: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        seen: set = set()
        clean: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []

        for sale in sales:
            # Silently skip media-only placeholders
            if self._is_media_only(sale):
                continue

            # Dedup key
            key = (sale.get("timestamp"), sale.get("sender"), sale.get("product"))
            if key in seen:
                errors.append({"record": sale, "reason": "Duplicate record detected."})
                continue
            seen.add(key)

            # Arithmetic check
            qty = sale.get("quantity")
            unit = sale.get("unit_price")
            total = sale.get("total_price")
            if qty and unit and total:
                expected = round(qty * unit, 2)
                if abs(expected - total) > 0.05 * total:
                    errors.append({
                        "record": sale,
                        "reason": f"Arithmetic mismatch: {qty} × {unit} = {expected}, but total_price = {total}.",
                    })
                    sale["total_price"] = expected  # Auto-correct

            # Flag only when there's a real product but no pricing info at all
            has_price = sale.get("unit_price") or sale.get("total_price")
            has_qty = sale.get("quantity")
            if sale.get("product") and not has_price and not has_qty:
                errors.append({
                    "record": sale,
                    "reason": "Partial sale: product identified but price and quantity are both missing.",
                })

            clean.append(sale)

        return clean, errors
