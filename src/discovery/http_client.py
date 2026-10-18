"""Robust HTTP client with retries, exponential backoff, and User-Agent rotation."""

import random
import time
import logging
from typing import Optional, Dict
import httpx

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "ORBIT-Research-Bot/1.0 (+https://github.com/orbit-engine/orbit; public academic intelligence)",
]


class RobustHttpClient:
    def __init__(
        self,
        timeout: float = 12.0,
        max_retries: int = 3,
        backoff_factor: float = 1.5,
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.client = httpx.Client(
            timeout=self.timeout,
            follow_redirects=True,
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
        )

    def _get_headers(self, custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        if custom_headers:
            headers.update(custom_headers)
        return headers

    def get(self, url: str, custom_headers: Optional[Dict[str, str]] = None) -> Optional[httpx.Response]:
        """Fetch URL with retries and exponential backoff."""
        attempt = 0
        while attempt < self.max_retries:
            try:
                headers = self._get_headers(custom_headers)
                resp = self.client.get(url, headers=headers)
                
                # Check rate limit
                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", 2 ** attempt))
                    logger.warning(f"Rate limited (429) on {url}. Backing off for {retry_after}s.")
                    time.sleep(retry_after)
                    attempt += 1
                    continue

                resp.raise_for_status()
                return resp
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                attempt += 1
                sleep_time = (self.backoff_factor ** attempt) + random.uniform(0.1, 0.5)
                logger.warning(f"HTTP attempt {attempt}/{self.max_retries} failed for {url}: {e}. Retrying in {sleep_time:.2f}s")
                if attempt >= self.max_retries:
                    logger.error(f"Failed to fetch {url} after {self.max_retries} attempts.")
                    return None
                time.sleep(sleep_time)
        return None

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
