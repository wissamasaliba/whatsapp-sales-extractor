"""
Raw WhatsApp chat parser.
Converts exported .txt content into a list of structured message dicts.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


# Matches both 12h and 24h WhatsApp timestamp formats:
# e.g. "12/31/24, 3:45 PM - " or "31/12/2024, 15:45 - "
TIMESTAMP_PATTERN = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2,4}),\s(\d{1,2}:\d{2}(?:\s?[AP]M)?)\s-\s"
)


@dataclass
class Message:
    """
    Represents a single parsed WhatsApp message.

    Attributes:
        timestamp: Date and time string as it appears in the export (e.g. "12/31/24, 3:45 PM").
        sender:    Display name of the message author. Empty string for system messages.
        text:      Full message body; multi-line messages are joined with newlines.
        is_system: True for WhatsApp system notices (e.g. encryption banner, group events).
        raw:       Original unmodified line(s) from the export file.
    """
    timestamp: str
    sender: str
    text: str
    is_system: bool = False
    raw: str = field(default="", repr=False)


def parse_chat(raw_text: str) -> List[Message]:
    """
    Parse raw WhatsApp export text into a list of Message objects.
    Multi-line messages are joined into a single text block.
    """
    lines = raw_text.splitlines()
    messages: List[Message] = []
    buffer: Optional[dict] = None

    for line in lines:
        match = TIMESTAMP_PATTERN.match(line)
        if match:
            if buffer:
                messages.append(_build_message(buffer))
            rest = line[match.end():]
            if ":" in rest:
                sender, _, text = rest.partition(":")
                buffer = {
                    "timestamp": f"{match.group(1)}, {match.group(2)}",
                    "sender": sender.strip(),
                    "text": text.strip(),
                    "is_system": False,
                    "raw": line,
                }
            else:
                # System message (e.g. "Messages and calls are end-to-end encrypted")
                buffer = {
                    "timestamp": f"{match.group(1)}, {match.group(2)}",
                    "sender": "",
                    "text": rest.strip(),
                    "is_system": True,
                    "raw": line,
                }
        elif buffer:
            # Continuation of a multi-line message
            buffer["text"] += "\n" + line
            buffer["raw"] += "\n" + line

    if buffer:
        messages.append(_build_message(buffer))

    return messages


def _build_message(buf: dict) -> Message:
    """
    Construct a Message dataclass instance from a raw buffer dict.

    Args:
        buf: Dict with keys timestamp, sender, text, is_system, raw.

    Returns:
        Fully populated Message instance.
    """
    return Message(
        timestamp=buf["timestamp"],
        sender=buf["sender"],
        text=buf["text"],
        is_system=buf["is_system"],
        raw=buf["raw"],
    )
