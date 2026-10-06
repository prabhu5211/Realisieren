import os
import sys
import subprocess
from pathlib import Path

# Automatically use the project's virtual environment if available and dependencies aren't in current environment
venv_executable = Path(__file__).parent / "venv" / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python")

if venv_executable.exists() and sys.executable.lower() != str(venv_executable.resolve()).lower():
    try:
        import requests
        import bs4
    except ImportError:
        # Re-execute script using the virtual environment Python interpreter
        result = subprocess.run([str(venv_executable)] + sys.argv[1:])
        sys.exit(result.returncode)

import csv
import json
import logging
import time
from datetime import datetime, timezone

from scrapers.books_scraper import BooksScraper
from scrapers.quotes_scraper import QuotesScraper
from processing.cleaning import clean_record
from processing.validation import validate_record
from processing.deduplication import generate_fingerprint

FIELDNAMES = [
    "source",
    "source_url",
    "name_or_title",
    "category",
    "price",
    "rating",
    "author",
    "tags",
    "description",
    "scraped_at",
]

def setup_logging():
    """Configures logging to write to both console and logs/scraper.log."""
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "scraper.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

def main():
    setup_logging()
    logger = logging.getLogger("main")
    logger.info("Starting ETL Pipeline for Books and Quotes scrapers")

    start_datetime = datetime.now(timezone.utc)
    start_time_sec = time.time()

    # Ensure output directory exists
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize metrics structure
    metrics = {
        "Books to Scrape": {
            "scraped": 0,
            "cleaned": 0,
            "valid": 0,
            "rejected": 0,
            "rejection_reasons": {},
            "duplicates": 0,
            "final": 0,
        },
        "Quotes to Scrape": {
            "scraped": 0,
            "cleaned": 0,
            "valid": 0,
            "rejected": 0,
            "rejection_reasons": {},
            "duplicates": 0,
            "final": 0,
        },
    }

    raw_records = []

    # 1. Scrape Books
    try:
        books_scraper = BooksScraper()
        books = books_scraper.scrape()
        metrics["Books to Scrape"]["scraped"] = len(books)
        raw_records.extend(books)
    except Exception as e:
        logger.error(f"BooksScraper failed completely: {e}", exc_info=True)

    # 2. Scrape Quotes
    try:
        quotes_scraper = QuotesScraper()
        quotes = quotes_scraper.scrape()
        metrics["Quotes to Scrape"]["scraped"] = len(quotes)
        raw_records.extend(quotes)
    except Exception as e:
        logger.error(f"QuotesScraper failed completely: {e}", exc_info=True)

    # 3. Clean & Validate Records
    valid_records = []
    seen_fingerprints = set()
    timestamp_str = start_datetime.strftime("%Y-%m-%d %H:%M:%SZ")

    for raw in raw_records:
        source = raw.get("source", "Unknown Source")
        if source not in metrics:
            metrics[source] = {
                "scraped": 1,
                "cleaned": 0,
                "valid": 0,
                "rejected": 0,
                "rejection_reasons": {},
                "duplicates": 0,
                "final": 0,
            }

        # Cleaning
        cleaned = clean_record(raw, timestamp=timestamp_str)
        metrics[source]["cleaned"] += 1

        # Validation
        reasons = validate_record(cleaned)
        if reasons:
            metrics[source]["rejected"] += 1
            for reason in reasons:
                metrics[source]["rejection_reasons"][reason] = (
                    metrics[source]["rejection_reasons"].get(reason, 0) + 1
                )
            logger.warning(f"Record rejected [{source}]: {reasons} | Raw: {raw}")
            continue

        metrics[source]["valid"] += 1

        # Deduplication
        fp = generate_fingerprint(cleaned)
        if fp in seen_fingerprints:
            metrics[source]["duplicates"] += 1
            logger.info(f"Duplicate record detected [{source}]: {cleaned.get('name_or_title')}")
        else:
            seen_fingerprints.add(fp)
            valid_records.append(cleaned)
            metrics[source]["final"] += 1

    # 4. Write final_dataset.csv
    csv_file = output_dir / "final_dataset.csv"
    logger.info(f"Writing {len(valid_records)} unique records to {csv_file}")

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, restval="")
        writer.writeheader()
        for rec in valid_records:
            # Standardize None values as empty strings for CSV writing
            formatted_rec = {k: ("" if v is None else v) for k, v in rec.items()}
            writer.writerow(formatted_rec)

    end_datetime = datetime.now(timezone.utc)
    duration_seconds = round(time.time() - start_time_sec, 2)

    # 5. Calculate overall metrics
    overall = {
        "scraped": sum(m["scraped"] for m in metrics.values()),
        "cleaned": sum(m["cleaned"] for m in metrics.values()),
        "valid": sum(m["valid"] for m in metrics.values()),
        "rejected": sum(m["rejected"] for m in metrics.values()),
        "rejection_reasons": {},
        "duplicates": sum(m["duplicates"] for m in metrics.values()),
        "final_total": len(valid_records),
    }

    for m in metrics.values():
        for reason, count in m["rejection_reasons"].items():
            overall["rejection_reasons"][reason] = (
                overall["rejection_reasons"].get(reason, 0) + count
            )

    summary_report = {
        "start_time": start_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end_time": end_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration_seconds": duration_seconds,
        "sources": metrics,
        "overall": overall,
    }

    # Write summary_report.json
    json_file = output_dir / "summary_report.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(summary_report, f, indent=2, ensure_ascii=False)

    logger.info(f"Summary report written to {json_file}")
    logger.info(
        f"ETL pipeline finished in {duration_seconds}s. Total final records: {overall['final_total']}"
    )

if __name__ == "__main__":
    main()
