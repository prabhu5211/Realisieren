import pytest
from processing.cleaning import (
    clean_text,
    strip_quotes,
    clean_price,
    clean_rating,
    clean_tags,
    normalize_url,
    clean_record,
)

def test_clean_text():
    assert clean_text(" Hello \n World ") == "Hello World"
    assert clean_text("Book\xa0Title") == "Book Title"
    assert clean_text(None) is None
    assert clean_text("   ") is None

def test_strip_quotes():
    assert strip_quotes("“The world as we have created it”") == "The world as we have created it"
    assert strip_quotes('"Hello"') == "Hello"
    assert strip_quotes(None) is None

def test_clean_price():
    assert clean_price("£51.77") == 51.77
    assert clean_price("$10.50") == 10.50
    assert clean_price(25) == 25.0
    assert clean_price("invalid") is None
    assert clean_price(None) is None

def test_clean_rating():
    assert clean_rating("Three") == 3
    assert clean_rating("one") == 1
    assert clean_rating("Five") == 5
    assert clean_rating("4") == 4
    assert clean_rating(2) == 2
    assert clean_rating("Ten") is None
    assert clean_rating(None) is None

def test_clean_tags():
    assert clean_tags(["Change", "World", "change"]) == "change;world"
    assert clean_tags(" tag2, Tag1 ") == "tag1;tag2"
    assert clean_tags([]) is None
    assert clean_tags(None) is None

def test_normalize_url():
    assert normalize_url("https://books.toscrape.com/index.html") == "https://books.toscrape.com/index.html"
    assert normalize_url("http://quotes.toscrape.com/") == "http://quotes.toscrape.com/"
    assert normalize_url("ftp://example.com") is None
    assert normalize_url(None) is None

def test_clean_record():
    raw = {
        "source": "Books to Scrape",
        "source_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
        "name_or_title": " A Light in the Attic\n ",
        "price": "£51.77",
        "rating": "Three",
    }
    cleaned = clean_record(raw, timestamp="2026-10-06T18:00:00Z")
    assert cleaned["name_or_title"] == "A Light in the Attic"
    assert cleaned["price"] == 51.77
    assert cleaned["rating"] == 3
    assert cleaned["scraped_at"] == "2026-10-06T18:00:00Z"
