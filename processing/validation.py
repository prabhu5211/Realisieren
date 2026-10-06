ALLOWED_SOURCES = {"Books to Scrape", "Quotes to Scrape"}

def validate_record(record: dict) -> list[str]:
    """
    Validates a cleaned record according to stage 6 requirements.
    Returns a list of error strings. An empty list indicates a valid record.
    """
    reasons = []

    # 1. Source check
    source = record.get("source")
    if not source or source not in ALLOWED_SOURCES:
        reasons.append(f"Invalid or missing source: '{source}'")

    # 2. Name/Title check
    name_or_title = record.get("name_or_title")
    if not name_or_title or not isinstance(name_or_title, str) or not name_or_title.strip():
        reasons.append("Missing or empty name_or_title")

    # 3. Valid URL check
    source_url = record.get("source_url")
    if not source_url or not isinstance(source_url, str) or not source_url.startswith(("http://", "https://")):
        reasons.append(f"Invalid source_url: '{source_url}'")

    # 4. Valid Price check (if present)
    price = record.get("price")
    if price is not None:
        if not isinstance(price, (int, float)) or price < 0:
            reasons.append(f"Invalid price value: {price} (must be numeric >= 0)")

    # 5. Valid Rating check (if present)
    rating = record.get("rating")
    if rating is not None:
        if not isinstance(rating, int) or not (1 <= rating <= 5):
            reasons.append(f"Invalid rating value: {rating} (must be integer 1 to 5)")

    return reasons
