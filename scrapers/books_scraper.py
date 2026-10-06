import logging
from urllib.parse import urljoin
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class BooksScraper(BaseScraper):
    """
    Scraper for Books to Scrape (https://books.toscrape.com/).
    Traverses pages dynamically using the 'next' link until all books are extracted.
    """

    START_URL = "https://books.toscrape.com/"
    SOURCE_NAME = "Books to Scrape"

    def scrape(self) -> list[dict]:
        """
        Scrapes all pages of Books to Scrape.
        Returns a list of raw dictionaries.
        """
        records = []
        current_url = self.START_URL
        page_count = 0

        while current_url:
            page_count += 1
            logger.info(f"Scraping Books page {page_count}: {current_url}")
            soup = self.fetch_page(current_url)

            if soup is None:
                logger.error(f"Stopping Books scraping due to fetch failure at page {page_count}: {current_url}")
                break

            pods = soup.select("article.product_pod")
            logger.info(f"Found {len(pods)} book records on page {page_count}")

            for pod in pods:
                try:
                    # Title & link from h3 > a
                    a_tag = pod.select_one("h3 > a")
                    title = a_tag.get("title") or a_tag.text.strip() if a_tag else None

                    rel_link = a_tag.get("href") if a_tag else None
                    detail_url = urljoin(current_url, rel_link) if rel_link else current_url

                    # Price from p.price_color
                    price_el = pod.select_one("p.price_color")
                    raw_price = price_el.text.strip() if price_el else None

                    # Rating from class attribute on p.star-rating (e.g. ['star-rating', 'Three'])
                    rating_el = pod.select_one("p.star-rating")
                    if rating_el and rating_el.get("class"):
                        class_list = rating_el.get("class")
                        # Rating word is usually the second class name
                        raw_rating = " ".join([c for c in class_list if c != "star-rating"])
                    else:
                        raw_rating = None

                    raw_record = {
                        "source": self.SOURCE_NAME,
                        "source_url": detail_url,
                        "name_or_title": title,
                        "category": None,
                        "price": raw_price,
                        "rating": raw_rating,
                        "author": None,
                        "tags": None,
                        "description": None,
                    }
                    records.append(raw_record)

                except Exception as e:
                    logger.warning(f"Error parsing a book pod on page {page_count}: {e}")
                    continue

            # Pagination: check for li.next > a
            next_tag = soup.select_one("li.next > a")
            if next_tag and next_tag.get("href"):
                current_url = urljoin(current_url, next_tag.get("href"))
            else:
                logger.info("No next page found for Books to Scrape. Pagination completed.")
                current_url = None

        logger.info(f"Total raw books scraped: {len(records)} over {page_count} pages")
        return records
