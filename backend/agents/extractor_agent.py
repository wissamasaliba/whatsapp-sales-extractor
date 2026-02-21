"""
ExtractorAgent: uses Groq (qwen/qwen3-32b) to extract structured sale records
from pre-filtered WhatsApp messages.
"""

import json
from typing import List, Dict, Any

from extractor import groq_client, MODEL, extract_sales_candidates

SYSTEM_PROMPT = """
You are a sales data extraction specialist. Your job is to read WhatsApp chat messages
and extract structured sale records from them.

For each sale found, return a JSON object with these fields:
- timestamp: the message timestamp (string)
- sender: who sent the message (string)
- product: product name or description (string)
- quantity: numeric quantity (number or null)
- unit_price: price per unit (number or null)
- total_price: total price of the transaction (number or null)
- currency: currency code or symbol detected (string or null)
- notes: any relevant extra info (string)

Return a JSON array of sale objects. If no sales are found, return an empty array [].
Do NOT include any text outside the JSON array.
"""


class ExtractorAgent:
    async def run(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Rule-based pre-filter to reduce API calls
        from parser import Message
        raw_messages = [
            Message(
                timestamp=m["timestamp"],
                sender=m["sender"],
                text=m["text"],
                is_system=m.get("is_system", False),
            )
            for m in messages
            if not m.get("is_system", False)
        ]
        candidates = extract_sales_candidates(raw_messages)

        if not candidates:
            return []

        # Group candidates into batches of 30 to stay within token limits
        batches = [candidates[i:i + 30] for i in range(0, len(candidates), 30)]
        all_sales: List[Dict[str, Any]] = []

        for batch in batches:
            batch_text = "\n---\n".join(
                f"[{c['timestamp']}] {c['sender']}: {c['text']}" for c in batch
            )
            response = groq_client.chat.completions.create(
                model=MODEL,
                max_tokens=4096,
                reasoning_effort="none",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": batch_text},
                ],
            )
            try:
                sales = json.loads(response.choices[0].message.content)
                if isinstance(sales, list):
                    all_sales.extend(sales)
            except json.JSONDecodeError:
                pass  # BugChecker will flag this batch

        return all_sales
