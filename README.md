# Web Scraping ETL Pipeline: Books & Quotes to Scrape

An end-to-end Python ETL (Extract, Transform, Load) pipeline that collects data from two practice websites ([Books to Scrape](https://books.toscrape.com/) and [Quotes to Scrape](https://quotes.toscrape.com/)), normalizes and validates heterogeneous web data into a unified schema, removes duplicates, and generates a clean CSV dataset alongside an execution summary report and logs.

---

## 1. Quick Start & Setup

### Prerequisites
* **Python**: Version 3.10, 3.11, or 3.12 (Tested on Python 3.12)
* **Virtual Environment**: `venv`

### Installation
1. Clone or open the repository folder:
   ```bash
   cd "path/to/project"
   ```
2. Create and activate a virtual environment:
   * **Windows (PowerShell)**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   * **macOS / Linux**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
3. Install dependencies from `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

### Execution
Run the entire ETL pipeline with a single command:
```bash
python main.py
```
*(If using the virtual environment directly: `.\venv\Scripts\python.exe main.py`)*

---

## 2. HTML Inspection & Selector Reference

Before building the scrapers, target websites were inspected to determine exact HTML element selectors:

| Item | Books to Scrape (`https://books.toscrape.com/`) | Quotes to Scrape (`https://quotes.toscrape.com/`) |
| :--- | :--- | :--- |
| **Record Container** | `article.product_pod` | `div.quote` |
| **Main Text / Title** | `h3 > a` (`title` attribute holds full title) | `span.text` (wrapped in curly quotes) |
| **Price** | `p.price_color` (e.g. `£51.77`) | *None* |
| **Rating** | Second class on `p.star-rating` (e.g. `Three`) | *None* |
| **Author** | *None* | `small.author` |
| **Tags** | *None* | `a.tag` (zero or more) |
| **Source URL / Link**| `h3 > a[href]` (relative path to detail page) | `a[href*="/author/"]` (author detail page) |
| **Next Page** | `li.next > a` | `li.next > a` |

---

## 3. Dynamic Pagination Mechanism

Neither scraper hardcodes page numbers (such as `range(1, 51)`). Instead, dynamic pagination follows these steps:
1. Start at the site home page URL.
2. Download and parse the HTML response with `BeautifulSoup`.
3. Extract all data records on the active page.
4. Locate the `li.next > a` navigation element.
5. If found, resolve its relative `href` path into an absolute URL using `urllib.parse.urljoin(current_url, href)` and loop.
6. If `li.next > a` is missing (`None`), pagination terminates gracefully.

---

## 4. Unified Data Model

Because books and quotes have different native structures, a common 10-column table layout is established. Empty/non-applicable fields are stored as `None` (written as empty cells in CSV):

| Column | Books to Scrape | Quotes to Scrape | Data Type |
| :--- | :--- | :--- | :--- |
| `source` | `"Books to Scrape"` | `"Quotes to Scrape"` | String |
| `source_url` | Book detail page absolute URL | Author detail page absolute URL | String |
| `name_or_title` | Full book title | Quote text (curly quotes removed) | String |
| `category` | `None` | `None` | String |
| `price` | Extracted float (e.g. `51.77`) | `None` | Float |
| `rating` | Extracted integer (1 to 5) | `None` | Integer |
| `author` | `None` | Author full name | String |
| `tags` | `None` | Lowercase, sorted, `;`-separated tags | String |
| `description` | `None` | `None` | String |
| `scraped_at` | UTC timestamp (`YYYY-MM-DD HH:MM:SSZ`) | UTC timestamp (`YYYY-MM-DD HH:MM:SSZ`) | String |

---

## 5. ETL Processing Stages

### Cleaning (`processing/cleaning.py`)
* `clean_text`: Strips leading/trailing spaces, newlines, tabs, and non-breaking spaces (`\xa0`). Collapses internal consecutive spaces into a single space.
* `strip_quotes`: Strips surrounding curly (`“`, `”`) and standard (`"`, `'`) quotes from quote strings.
* `clean_price`: Parses numeric price values using regex `r"(\d+\.\d+|\d+)"` (e.g. `"£51.77"` $\rightarrow$ `51.77`).
* `clean_rating`: Maps word ratings (`"One"` $\rightarrow$ 1, `"Two"` $\rightarrow$ 2, `"Three"` $\rightarrow$ 3, `"Four"` $\rightarrow$ 4, `"Five"` $\rightarrow$ 5).
* `clean_tags`: Lowercases, deduplicates, sorts alphabetically, and joins tag lists with `;` (e.g. `["Change", "World"]` $\rightarrow$ `"change;world"`).
* `normalize_url`: Validates and formats complete HTTP/HTTPS URLs.

### Validation (`processing/validation.py`)
Checks each record against strict quality rules and returns rejection reason strings:
1. **Source**: Must equal `"Books to Scrape"` or `"Quotes to Scrape"`.
2. **Title/Name**: Must be a non-empty string.
3. **URL**: Must start with `http://` or `https://`.
4. **Price**: If present, must be numeric $\ge 0$.
5. **Rating**: If present, must be integer $1 \le \text{rating} \le 5$.

Invalid records are rejected, logged with warnings, and tallied by rejection reason in the summary report.

### Deduplication (`processing/deduplication.py`)
Records are fingerprinted using a deterministic SHA-256 hash computed over normalized fields:
* **Books**: `SHA-256("books|" + source_norm + "|" + title_norm)`
* **Quotes**: `SHA-256("quotes|" + source_norm + "|" + author_norm + "|" + quote_first_50_chars)`

Duplicate records are filtered out (dropped) to guarantee dataset uniqueness while maintaining duplicate counts in `summary_report.json`.

---

## 6. Resilience & Networking

* **Session Management**: Uses `requests.Session()` with custom User-Agent headers.
* **Automatic Retries**: Implements `urllib3` Retry adapter configured for 3 attempts with exponential backoff (1s, 2s, 4s) on HTTP status codes `[429, 500, 502, 503, 504]`.
* **Rate Limiting**: Pauses `0.5` seconds between HTTP requests to avoid server strain.
* **Fault Tolerance**: Wrapping source scrapers and individual item parsing blocks in `try/except` ensures that if a network request times out or a single item fails, the error is logged and the pipeline continues processing remaining data.

---

## 7. Outputs & Artifacts

Running `python main.py` generates:
1. `output/final_dataset.csv`: Clean, unified CSV containing valid, unique records.
2. `output/summary_report.json`: Execution metadata including counts (scraped, cleaned, valid, rejected, duplicates, final total) per source and overall runtime.
3. `logs/scraper.log`: Detailed timestamped logs of requests, page transitions, warnings, and errors.

---

## 8. Unit Testing

Run unit tests without internet access:
```bash
pytest
```
Tests verify cleaning functions, validation edge cases, and duplicate fingerprinting.

---

## 9. Known Assumptions & Limitations

* **Book Categories & Descriptions**: Books to Scrape catalog pages list 20 books per page with title, price, and rating, but omit category and description details (which require visiting 1,000 separate detail pages). To respect server load and keep execution fast, category and description are set to `None` for catalog items as permitted by the specification.
