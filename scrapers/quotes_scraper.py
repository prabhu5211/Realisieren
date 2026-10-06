import logging
from urllib.parse import urljoin
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class QuotesScraper(BaseScraper):
    """
    Scraper for Quotes to Scrape (https://quotes.toscrape.com/).
    Traverses pages dynamically using the 'next' link until all quotes are extracted.
    """

    START_URL = "https://quotes.toscrape.com/"
    SOURCE_NAME = "Quotes to Scrape"

    def scrape(self) -> list[dict]:
        """
        Scrapes all pages of Quotes to Scrape.
        Returns a list of raw dictionaries.
        """
        records = []
        current_url = self.START_URL
        page_count = 0

        while current_url:
            page_count += 1
            logger.info(f"Scraping Quotes page {page_count}: {current_url}")
            soup = self.fetch_page(current_url)

            if soup is None:
                logger.error(f"Stopping Quotes scraping due to fetch failure at page {page_count}: {current_url}")
                break

            quote_divs = soup.select("div.quote")
            logger.info(f"Found {len(quote_divs)} quote records on page {page_count}")

            for q_div in quote_divs:
                try:
                    # Main quote text from span.text
                    text_el = q_div.select_one("span.text")
                    quote_text = text_el.text.strip() if text_el else None

                    # Author from small.author
                    author_el = q_div.select_one("small.author")
                    author_name = author_el.text.strip() if author_el else None

                    # Tags from a.tag
                    tag_els = q_div.select("a.tag")
                    tags_list = [t.text.strip() for t in tag_els] if tag_els else []

                    # Source URL: author detail URL if available, else current page URL
                    author_link_el = q_div.select_one('a[href*="/author/"]')
                    if author_link_el and author_link_el.get("href"):
                        source_url = urljoin(current_url, author_link_el.get("href"))
                    else:
                        source_url = current_url

                    raw_record = {
                        "source": self.SOURCE_NAME,
                        "source_url": source_url,
                        "name_or_title": quote_text,
                        "category": None,
                        "price": None,
                        "rating": None,
                        "author": author_name,
                        "tags": tags_list,
                        "description": None,
                    }
                    records.append(raw_record)

                except Exception as e:
                    logger.warning(f"Error parsing a quote div on page {page_count}: {e}")
                    continue

            # Pagination: check for li.next > a
            next_tag = soup.select_one("li.next > a")
            if next_tag and next_tag.get("href"):
                current_url = urljoin(current_url, next_tag.get("href"))
            else:
                logger.info("No next page found for Quotes to Scrape. Pagination completed.")
                current_url = None

        logger.info(f"Total raw quotes scraped: {len(records)} over {page_count} pages")
        return records
