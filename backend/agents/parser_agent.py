"""
ParserAgent: wraps the rule-based parser and enriches messages with
basic metadata (language hint, message type) using the Groq API.
"""

import json
from typing import List, Dict, Any

from extractor import groq_client, MODEL
from parser import parse_chat, Message


class ParserAgent:
    async def run(self, raw_text: str) -> List[Dict[str, Any]]:
        """
        Parse raw WhatsApp export text into a list of message dicts.

        Args:
            raw_text: Full string contents of the .txt export file.

        Returns:
            List of dicts with keys: timestamp, sender, text, is_system.
        """
        messages = parse_chat(raw_text)
        return [self._to_dict(m) for m in messages]

    def _to_dict(self, msg: Message) -> Dict[str, Any]:
        """
        Serialize a Message dataclass to a plain dict for downstream agents.

        Args:
            msg: Parsed Message instance.

        Returns:
            Dict with keys: timestamp, sender, text, is_system.
        """
        return {
            "timestamp": msg.timestamp,
            "sender": msg.sender,
            "text": msg.text,
            "is_system": msg.is_system,
        }

    async def classify_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Optional: use Groq to classify a batch of messages as sale-related or not.
        Call this when rule-based heuristics produce too many false positives.
        """
        if not messages:
            return messages

        batch_text = "\n---\n".join(
            f"[{m['timestamp']}] {m['sender']}: {m['text']}" for m in messages[:50]
        )

        response = groq_client.chat.completions.create(
            model=MODEL,
            max_tokens=1024,
            reasoning_effort="none",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a sales data classifier. "
                        "Given a list of WhatsApp messages separated by '---', "
                        "return a JSON array where each element is true if the corresponding "
                        "message is related to a sale (product, price, quantity, order, payment) "
                        "or false otherwise. Return ONLY the JSON array, no explanation."
                    ),
                },
                {"role": "user", "content": batch_text},
            ],
        )

        try:
            flags = json.loads(response.choices[0].message.content)
            for msg, flag in zip(messages, flags):
                msg["is_sale_related"] = bool(flag)
        except Exception:
            pass  # Fall back to keeping all messages

        return messages
