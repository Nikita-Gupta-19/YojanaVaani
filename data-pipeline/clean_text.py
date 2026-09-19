"""
Text cleaning and entity unescaping utilities for YojanaVaani data pipeline.

Cleans recursive HTML entities (e.g. &amp;amp;#39; -> '), strips repeated Slate markdown
list numbering artifacts (e.g. repeated '1. '), and normalizes whitespace so that
TTS, embeddings, and structured parsers receive clean, natural text.
"""

import html
import json
import os
import re
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def clean_html_entities(text: str) -> str:
    """
    Recursively unescapes HTML entities until stable.
    Handles double- and triple-encoded entities such as '&amp;amp;#39;'.
    """
    if not text or not isinstance(text, str):
        return "" if text is None else str(text)

    # Collapse repeated &amp; sequences first
    text = re.sub(r'(&amp;)+', '&', text)

    prev = text
    while True:
        unescaped = html.unescape(prev)
        if unescaped == prev:
            break
        prev = unescaped
    return prev


def normalize_markdown_artifacts(text: str) -> str:
    """
    Normalizes whitespace and cleans repeated Slate-generated '1.' list markers.
    Converts repetitive '   1. ' list items into clean markdown bullet points.
    """
    if not text:
        return ""

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Check if lines have repeated '1.' prefixes (Slate markdown artifact)
    lines = text.split("\n")
    cleaned_lines = []
    
    for line in lines:
        # Match indentation + '1.' or '1)'
        match = re.match(r'^(\s*)1[\.\)]\s+(.*)$', line)
        if match:
            # Convert repetitive '1. ' to bullet point with minimal clean indent
            indent = match.group(1)
            content = match.group(2)
            # If deeply indented Slate artifact, normalize to standard bullet
            clean_indent = "  " if len(indent) >= 3 else ""
            cleaned_lines.append(f"{clean_indent}- {content}")
        else:
            cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)

    # Normalize multiple blank lines (max 2 consecutive newlines)
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove leading/trailing whitespace
    return text.strip()


def clean_text(text: str) -> str:
    """Full cleaning pipeline for a text string: unescapes HTML entities and normalizes markdown."""
    if not text:
        return ""
    text = clean_html_entities(text)
    text = normalize_markdown_artifacts(text)
    return text


def clean_scheme_record(scheme: dict) -> dict:
    """
    Recursively cleans all text fields in a scheme dictionary.
    Returns a new cleaned dictionary without mutating in-place.
    """
    cleaned = dict(scheme)

    # Clean top-level text fields
    if "name" in cleaned and cleaned["name"]:
        cleaned["name"] = clean_html_entities(cleaned["name"]).strip()
    if "category" in cleaned and cleaned["category"]:
        cleaned["category"] = clean_html_entities(cleaned["category"]).strip()
    if "ministry_or_department" in cleaned and cleaned["ministry_or_department"]:
        cleaned["ministry_or_department"] = clean_html_entities(cleaned["ministry_or_department"]).strip()
    if "description" in cleaned and cleaned["description"]:
        cleaned["description"] = clean_text(cleaned["description"])
    if "benefits" in cleaned:
        cleaned["benefits"] = clean_text(cleaned.get("benefits", ""))
    if "application_process" in cleaned:
        cleaned["application_process"] = clean_text(cleaned.get("application_process", ""))
    if "contact_information" in cleaned and cleaned["contact_information"]:
        cleaned["contact_information"] = clean_text(cleaned["contact_information"])
    if "source_text" in cleaned and cleaned["source_text"]:
        cleaned["source_text"] = clean_text(cleaned["source_text"])

    # Clean required_documents list
    if "required_documents" in cleaned and isinstance(cleaned["required_documents"], list):
        cleaned["required_documents"] = [
            clean_text(doc) for doc in cleaned["required_documents"] if doc
        ]

    # Clean eligibility_criteria
    if "eligibility_criteria" in cleaned and isinstance(cleaned["eligibility_criteria"], dict):
        elig = dict(cleaned["eligibility_criteria"])
        if "other_conditions_text" in elig:
            elig["other_conditions_text"] = clean_text(elig.get("other_conditions_text", ""))
        cleaned["eligibility_criteria"] = elig

    return cleaned


def clean_all_schemes(data_path: str = None) -> list[dict]:
    """Loads schemes JSON, applies full cleaning across all records, and saves the result."""
    if data_path is None:
        data_path = os.path.join(os.path.dirname(__file__), "data", "scraped_schemes.json")

    if not os.path.exists(data_path):
        logger.error(f"File not found: {data_path}")
        return []

    with open(data_path, "r", encoding="utf-8") as f:
        schemes = json.load(f)

    logger.info(f"Cleaning text and unescaping HTML entities across {len(schemes)} schemes...")
    cleaned_schemes = [clean_scheme_record(s) for s in schemes]

    # Count corrupted entities remaining
    remaining_entities = 0
    for s in cleaned_schemes:
        dumped = json.dumps(s)
        if any(e in dumped for e in ["&amp;", "&#39;", "&quot;", "&gt;", "&lt;"]):
            remaining_entities += 1

    logger.info(f"Entities remaining after cleaning: {remaining_entities} (Target: 0)")

    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(cleaned_schemes, f, indent=2, ensure_ascii=False)

    logger.info(f"Successfully saved {len(cleaned_schemes)} cleaned schemes to {data_path}")
    return cleaned_schemes


if __name__ == "__main__":
    clean_all_schemes()
