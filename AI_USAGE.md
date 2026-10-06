# AI Usage & Transparency Log

This document details how AI assistance (Google Antigravity AI Assistant powered by Gemini 3.6 Flash) was utilized in designing, implementing, and verifying the Web Scraping ETL Pipeline.

---

## 1. Overview of AI Assistance
AI was used as a pair programming assistant throughout the development process for:
* **Architecture Planning**: Structuring a 3-tier ETL pipeline (`scrapers/`, `processing/`, `main.py`, `tests/`).
* **Boilerplate & Helper Generation**: Crafting resilient HTTP session wrappers with `urllib3` retry backoff policies.
* **Regular Expressions**: Designing regex patterns for currency extraction (`r"(\d+\.\d+|\d+)"`) and tag normalization.
* **Test Suite Design**: Generating unit tests for data cleaning edge cases, validation rules, and SHA-256 fingerprinting.
* **Documentation**: Structuring `README.md` and `AI_USAGE.md`.

---

## 2. Sample Prompts Used

### Prompt 1: Project Setup & Architecture
> *"Build a Python ETL pipeline for Books to Scrape and Quotes to Scrape adhering to the Reference Document specification. Use standard packages (requests, bs4, lxml, pytest) and separate scrapers from cleaning, validation, deduplication, and execution."*

### Prompt 2: Cleaning & Validation Functions
> *"Write pure functions in processing/cleaning.py to clean prices from currency strings, map rating words ('Three' -> 3), strip curly quotes, and format tags. Write processing/validation.py to check source, title, price, rating, and source_url."*

### Prompt 3: Resilient Scraping & Deduplication
> *"Create scrapers/base_scraper.py with requests.Session, exponential retries for status codes 429/500/502/503/504, rate limiting pauses, and explicit utf-8 encoding. Implement SHA-256 fingerprinting in processing/deduplication.py."*

---

## 3. Human Review & Corrections Applied

All AI-generated code was thoroughly inspected, tested, and adjusted to guarantee correctness:

1. **Character Encoding Fix**:
   * *AI Output*: Used default `response.text` without setting encoding explicitly.
   * *Review & Fix*: Forced `response.encoding = "utf-8"` in `BaseScraper.fetch_page()` to prevent British Pound symbols (`£`) from parsing as corrupted UTF-8 bytes (`Â£`).
2. **Ratings Extraction Handling**:
   * *AI Output*: Tried to read rating text directly from child elements.
   * *Review & Fix*: BeautifulSoup returns `p.star-rating` class attribute as a list (e.g. `['star-rating', 'Three']`). Updated `BooksScraper` to extract the rating word from the class array.
3. **Quote URL Resolution**:
   * *AI Output*: Used current page URL as source URL for quotes.
   * *Review & Fix*: Enhanced `QuotesScraper` to inspect `a[href*="/author/"]` and resolve full absolute author detail URLs using `urllib.parse.urljoin()`.
4. **CSV Formatter Formatting**:
   * *AI Output*: `None` values printed as literal string `"None"` in CSV.
   * *Review & Fix*: Updated `main.py` writer loop to map `None` values to empty strings `""` for tidy CSV presentation.

---

## 4. Verification & Testing

The code was validated end-to-end:
1. **Isolated Unit Tests**: Executed `pytest` across `tests/test_cleaning.py`, `tests/test_validation.py`, and `tests/test_deduplication.py` (14/14 tests passed in 0.36s).
2. **Fresh Execution Test**: Ran `python main.py` in a clean Python 3.12 virtual environment.
3. **Data Reconciliation**: Confirmed that `output/final_dataset.csv` contains 1,079 valid unique records (999 books, 80 quotes) and matches all counts recorded in `output/summary_report.json`.
