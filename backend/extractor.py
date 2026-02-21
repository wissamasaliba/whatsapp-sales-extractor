"""
Rule-based sales extractor.
Used as a fast pre-pass before the AI agents process the messages.
The Groq client is initialised here and shared by agent modules.
"""

import os
import re
from typing import List, Dict, Any

from groq import Groq
from parser import Message

# Shared Groq client — imported by agent modules
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "qwen/qwen3-32b"

# Common currency symbols and codes
CURRENCY_RE = re.compile(
    r"(?:R\$|USD|BRL|EUR|GBP|\$|€|£)?\s*\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?",
    re.IGNORECASE,
)

QUANTITY_RE = re.compile(r"\b(\d+)\s*(?:un|pcs?|pieces?|units?|caixas?|boxes?)\b", re.IGNORECASE)

PRODUCT_KEYWORDS = [
    "produto", "product", "item", "ref", "código", "code", "sku",
]


def extract_sales_candidates(messages: List[Message]) -> List[Dict[str, Any]]:
    """
    Return messages that likely contain sales information (price mentions, quantities, etc.).
    Each candidate is a dict with the original message plus extracted hints.
    """
    candidates = []

    for msg in messages:
        if msg.is_system:
            continue

        text = msg.text
        prices = CURRENCY_RE.findall(text)
        quantities = QUANTITY_RE.findall(text)

        if prices or quantities:
            candidates.append(
                {
                    "timestamp": msg.timestamp,
                    "sender": msg.sender,
                    "text": text,
                    "hint_prices": prices,
                    "hint_quantities": quantities,
                }
            )

    return candidates


def normalize_price(raw: str) -> float:
    """Strip non-numeric chars and return a float."""
    cleaned = re.sub(r"[^\d,.]", "", raw)
    # Handle Brazilian format: 1.234,56 → 1234.56
    if re.search(r"\d{1,3}\.\d{3},\d{2}$", cleaned):
        cleaned = cleaned.replace(".", "").replace(",", ".")
    else:
        cleaned = cleaned.replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0
