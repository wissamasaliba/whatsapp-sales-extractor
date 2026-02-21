"""
Orchestrator: coordinates the full pipeline.

Pipeline:
  raw text
    → ParserAgent   (structure messages)
    → ExtractorAgent (identify sale records)
    → ValidatorAgent (clean & validate fields)
    → BugChecker    (flag anomalies / inconsistencies)
    → final result
"""

from typing import Any, Dict
from agents.parser_agent import ParserAgent
from agents.extractor_agent import ExtractorAgent
from agents.validator_agent import ValidatorAgent
from agents.bug_checker import BugChecker


class Orchestrator:
    def __init__(self):
        """Instantiate all four pipeline agents."""
        self.parser = ParserAgent()
        self.extractor = ExtractorAgent()
        self.validator = ValidatorAgent()
        self.bug_checker = BugChecker()

    async def run(self, raw_text: str, filename: str = "") -> Dict[str, Any]:
        """
        Execute the full extraction pipeline on raw WhatsApp chat text.

        Args:
            raw_text: Full contents of the WhatsApp .txt export file.
            filename: Original uploaded filename, included verbatim in the response.

        Returns:
            Dict with keys:
              filename        — original filename
              sales           — list of validated sale dicts
              errors          — list of flagged issue dicts
              stats           — message_parsed, candidates_found, valid_sales, flagged_errors counts
        """
        # Step 1: Parse raw WhatsApp text into messages
        messages = await self.parser.run(raw_text)

        # Step 2: Extract candidate sale records from messages
        candidates = await self.extractor.run(messages)

        # Step 3: Validate and normalise each candidate
        validated = await self.validator.run(candidates)

        # Step 4: Check for bugs / anomalies across the full set
        result = await self.bug_checker.run(validated)

        return {
            "filename": filename,
            "sales": result["sales"],
            "errors": result["errors"],
            "stats": {
                "messages_parsed": len(messages),
                "candidates_found": len(candidates),
                "valid_sales": len(result["sales"]),
                "flagged_errors": len(result["errors"]),
            },
        }
