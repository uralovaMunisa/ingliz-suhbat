import re
from typing import List, Dict, Optional, Any


class ResponseParser:
    """Helper for extracting structured corrections and vocabulary from Emma's responses."""

    @staticmethod
    def extract_mistakes(text: str) -> List[Dict[str, str]]:
        mistakes = []
        correction_block = re.search(r"✏️\s*\*\*Correction:\*\*(.*?)(?=\n\s*(?:📚|🎯|$))", text, re.DOTALL | re.IGNORECASE)
        if not correction_block:
            return mistakes

        block_text = correction_block.group(1).strip()
        if "Perfect sentence" in block_text or "No mistakes" in block_text:
            return mistakes

        pair_pattern = re.compile(
            r"-\s*❌\s*(.+?)\s*→\s*✅\s*(.+?)(?:\n|$)(?:-\s*💡\s*(.+?)(?:\n|$))?",
            re.MULTILINE
        )

        for match in pair_pattern.finditer(block_text):
            original = match.group(1).strip().strip("*_")
            corrected = match.group(2).strip().strip("*_")
            explanation = match.group(3).strip() if match.group(3) else "Use the correct grammatical form."
            mistakes.append({
                "original": original,
                "corrected": corrected,
                "explanation": explanation
            })

        return mistakes

    @staticmethod
    def extract_vocabulary(text: str) -> Optional[Dict[str, str]]:
        # Matches: 📚 **New word/phrase:** "[phrase]" = [definition]. *Example: [example]*
        vocab_match = re.search(
            r"📚\s*\*\*New\s+.*?:(?:\*\*)?\s*[\"“]?([^\"”\n=]+)[\"”]?\s*=\s*(.+?)\.\s*\*?Example:\*?\s*(.+?)(?:\n\n|\n🎯|$|\Z)",
            text,
            re.DOTALL | re.IGNORECASE
        )
        if vocab_match:
            return {
                "phrase": vocab_match.group(1).strip(),
                "definition": vocab_match.group(2).strip(),
                "example": vocab_match.group(3).strip().strip("*_")
            }
        return None

    @staticmethod
    def has_corrections(text: str) -> bool:
        return "❌" in text and "✅" in text
