import pytest
from processing.deduplication import generate_fingerprint, deduplicate_records

def test_fingerprint_matching():
    b1 = {"source": "Books to Scrape", "name_or_title": "Example Book Title"}
    b2 = {"source": "Books to Scrape", "name_or_title": " Example Book Title "}
    b3 = {"source": "Books to Scrape", "name_or_title": "EXAMPLE BOOK TITLE!"}
    
    fp1 = generate_fingerprint(b1)
    fp2 = generate_fingerprint(b2)
    fp3 = generate_fingerprint(b3)
    
    assert fp1 == fp2 == fp3

def test_deduplicate_records():
    sample_records = [
        {"source": "Books to Scrape", "name_or_title": "Example Book Title", "price": 10.0},
        {"source": "Books to Scrape", "name_or_title": " Example Book Title ", "price": 10.0},
        {"source": "Quotes to Scrape", "author": "Albert Einstein", "name_or_title": "The world as we have created it..."},
        {"source": "Quotes to Scrape", "author": "Albert Einstein", "name_or_title": "THE WORLD AS WE HAVE CREATED IT..."},
        {"source": "Quotes to Scrape", "author": "Isaac Newton", "name_or_title": "If I have seen further..."},
    ]
    
    unique, duplicates = deduplicate_records(sample_records)
    assert len(unique) == 3
    assert duplicates == 2
