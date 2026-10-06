import hashlib
import re

def _normalize_for_fingerprint(text: str | None) -> str:
    """
    Lowercases, removes punctuation, and collapses whitespace for fingerprinting.
    """
    if not text:
        return ""
    text_lower = text.lower()
    # Remove punctuation
    text_no_punct = re.sub(r"[^\w\s]", "", text_lower)
    # Collapse multiple whitespaces
    return re.sub(r"\s+", " ", text_no_punct).strip()

def generate_fingerprint(record: dict) -> str:
    """
    Builds a unique SHA-256 fingerprint for a record.
    - Books: source + title
    - Quotes: source + author + first 50 chars of quote text
    """
    source = record.get("source", "")
    source_norm = _normalize_for_fingerprint(source)

    if source == "Books to Scrape":
        title_norm = _normalize_for_fingerprint(record.get("name_or_title", ""))
        raw_key = f"books|{source_norm}|{title_norm}"
    elif source == "Quotes to Scrape":
        author_norm = _normalize_for_fingerprint(record.get("author", ""))
        quote_norm = _normalize_for_fingerprint(record.get("name_or_title", ""))[:50]
        raw_key = f"quotes|{source_norm}|{author_norm}|{quote_norm}"
    else:
        # Fallback for generic sources
        title_norm = _normalize_for_fingerprint(record.get("name_or_title", ""))
        raw_key = f"generic|{source_norm}|{title_norm}"

    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

def deduplicate_records(records: list[dict]) -> tuple[list[dict], int]:
    """
    Removes duplicate records based on fingerprints.
    Returns a tuple: (unique_records, duplicate_count).
    """
    seen_fingerprints = set()
    unique_records = []
    duplicate_count = 0

    for rec in records:
        fp = generate_fingerprint(rec)
        if fp in seen_fingerprints:
            duplicate_count += 1
        else:
            seen_fingerprints.add(fp)
            unique_records.append(rec)

    return unique_records, duplicate_count
