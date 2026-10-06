import re
from datetime import datetime, timezone

RATING_MAP = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
}

def clean_text(value: str | None) -> str | None:
    """
    Removes extra spaces, tabs, newlines, and non-breaking spaces (\xa0).
    """
    if value is None:
        return None
    # Replace non-breaking space and convert multiple whitespaces to single space
    cleaned = str(value).replace("\xa0", " ").strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned if cleaned else None

def strip_quotes(value: str | None) -> str | None:
    """
    Removes surrounding curly and standard quotation marks around text.
    """
    cleaned = clean_text(value)
    if not cleaned:
        return None
    # Strip curly quotes and regular quotation marks
    return cleaned.strip('“”"\'')

def clean_price(value: str | float | int | None) -> float | None:
    """
    Converts currency string e.g. '£51.77' into float 51.77.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    
    text = str(value)
    match = re.search(r"(\d+\.\d+|\d+)", text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None

def clean_rating(value: str | int | float | None) -> int | None:
    """
    Converts rating words ('Three') or numeric representations ('3') to int (1..5).
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        val_int = int(value)
        return val_int if 1 <= val_int <= 5 else None

    text = str(value).strip().lower()
    # Check word map
    if text in RATING_MAP:
        return RATING_MAP[text]
    
    # Try parsing numeric digit from string
    match = re.search(r"\b([1-5])\b", text)
    if match:
        return int(match.group(1))
        
    return None

def clean_tags(value: list[str] | str | None) -> str | None:
    """
    Lowercases, sorts, and joins tags with ';'.
    """
    if not value:
        return None

    if isinstance(value, str):
        # Split by semicolon or comma if passed as string
        raw_list = re.split(r"[;,]", value)
    elif isinstance(value, list):
        raw_list = value
    else:
        return None

    cleaned_set = set()
    for tag in raw_list:
        c_tag = clean_text(str(tag))
        if c_tag:
            cleaned_set.add(c_tag.lower())

    if not cleaned_set:
        return None

    sorted_tags = sorted(list(cleaned_set))
    return ";".join(sorted_tags)

def normalize_url(value: str | None) -> str | None:
    """
    Ensures URL is complete and starts with http:// or https://.
    """
    cleaned = clean_text(value)
    if not cleaned:
        return None
    if cleaned.startswith(("http://", "https://")):
        return cleaned
    return None

def clean_record(raw_record: dict, timestamp: str | None = None) -> dict:
    """
    Applies all cleaning functions to a raw record dictionary and returns a cleaned record dict.
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

    source = clean_text(raw_record.get("source"))
    name_or_title = clean_text(raw_record.get("name_or_title"))
    
    # If source is Quotes to Scrape, strip surrounding curly quotes from title
    if source == "Quotes to Scrape" and name_or_title:
        name_or_title = strip_quotes(name_or_title)

    cleaned_dict = {
        "source": source,
        "source_url": normalize_url(raw_record.get("source_url")),
        "name_or_title": name_or_title,
        "category": clean_text(raw_record.get("category")),
        "price": clean_price(raw_record.get("price")),
        "rating": clean_rating(raw_record.get("rating")),
        "author": clean_text(raw_record.get("author")),
        "tags": clean_tags(raw_record.get("tags")),
        "description": clean_text(raw_record.get("description")),
        "scraped_at": timestamp,
    }
    return cleaned_dict
