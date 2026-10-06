import logging
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class BaseScraper:
    """
    Base web scraper providing a resilient HTTP session, retry logic,
    custom User-Agent, and rate limiting (pause between requests).
    """

    def __init__(self, pause_seconds: float = 0.5, timeout: float = 10.0):
        self.pause_seconds = pause_seconds
        self.timeout = timeout
        self.session = requests.Session()

        # Set standard browser user agent
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        })

        # Configure retries with exponential backoff for temporary errors
        retries = Retry(
            total=3,
            backoff_factor=1.0,  # Delays: 1s, 2s, 4s
            status_forcelist=[429, 500, 502, 503, 504],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def fetch_page(self, url: str) -> BeautifulSoup | None:
        """
        Fetch HTML from url and return a BeautifulSoup object.
        Pauses for pause_seconds before requesting to respect server limits.
        """
        time.sleep(self.pause_seconds)
        logger.info(f"Fetching page: {url}")

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            # Explicitly force utf-8 encoding to handle currency symbols (£) correctly
            response.encoding = "utf-8"
            return BeautifulSoup(response.text, "lxml")

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
