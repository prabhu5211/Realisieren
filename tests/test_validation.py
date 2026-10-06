import pytest
from processing.validation import validate_record

def test_valid_record():
    valid_record = {
        "source": "Books to Scrape",
        "source_url": "https://books.toscrape.com/catalogue/book_1/index.html",
        "name_or_title": "A Light in the Attic",
        "price": 51.77,
        "rating": 3,
    }
    reasons = validate_record(valid_record)
    assert reasons == []

def test_invalid_source():
    record = {
        "source": "Unknown Site",
        "source_url": "https://example.com",
        "name_or_title": "Sample Title",
    }
    reasons = validate_record(record)
    assert len(reasons) == 1
    assert "Invalid or missing source" in reasons[0]

def test_missing_title():
    record = {
        "source": "Quotes to Scrape",
        "source_url": "https://quotes.toscrape.com",
        "name_or_title": "",
    }
    reasons = validate_record(record)
    assert any("Missing or empty name_or_title" in r for r in reasons)

def test_invalid_price_and_rating():
    record = {
        "source": "Books to Scrape",
        "source_url": "https://books.toscrape.com",
        "name_or_title": "Test Book",
        "price": -10.0,
        "rating": 6,
    }
    reasons = validate_record(record)
    assert len(reasons) == 2
    assert any("Invalid price value" in r for r in reasons)
    assert any("Invalid rating value" in r for r in reasons)

def test_invalid_url():
    record = {
        "source": "Quotes to Scrape",
        "source_url": "ftp://invalid-url.com",
        "name_or_title": "Quote text",
    }
    reasons = validate_record(record)
    assert any("Invalid source_url" in r for r in reasons)
