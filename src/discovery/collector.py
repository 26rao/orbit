"""Autonomous discovery collector for public feeds and web articles."""

import argparse
import datetime
import logging
import sys
from typing import List, Dict, Any

from src.discovery.http_client import RobustHttpClient
from src.discovery.feed_parser import parse_feed_xml
from src.extraction.extractor import clean_html, compute_content_hash
from src.semantic.novelty import is_novel
from src.knowledge.db import init_db, insert_source, get_source_count, get_recent_titles

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("orbit.collector")

# High-quality, reliable, free public sources
DEFAULT_FEEDS = [
    {
        "name": "arXiv CS.AI",
        "url": "https://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=submittedDate&sortOrder=descending&max_results=15",
        "category": "academic",
    },
    {
        "name": "arXiv CS.LG (Machine Learning)",
        "url": "https://export.arxiv.org/api/query?search_query=cat:cs.LG&sortBy=submittedDate&sortOrder=descending&max_results=15",
        "category": "academic",
    },
    {
        "name": "Hacker News (Newest)",
        "url": "https://news.ycombinator.com/newest",
        "category": "signals",
        "is_html": True,  # Will parse HTML listing
    },
    {
        "name": "MIT Technology Review",
        "url": "https://www.technologyreview.com/feed/",
        "category": "emerging_tech",
    },
    {
        "name": "TechCrunch (Venture & AI)",
        "url": "https://techcrunch.com/feed/",
        "category": "industry",
    },
]


def extract_hn_links(html: str) -> List[Dict[str, Any]]:
    """Helper to extract top article links directly from Hacker News HTML."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for titleline in soup.find_all("span", class_="titleline"):
        a_tag = titleline.find("a")
        if a_tag and a_tag.get("href"):
            href = a_tag["href"]
            title = a_tag.get_text(strip=True)
            if href.startswith("http"):
                items.append({
                    "title": title,
                    "url": href,
                    "published": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "summary": title,
                    "source_name": "Hacker News",
                })
    return items


def run_collection_cycle(
    feeds: List[Dict[str, Any]] = None,
    max_items_per_feed: int = 15,
    fetch_full_page: bool = True,
    db_path: str = "data/orbit.db",
) -> Dict[str, Any]:
    """Execute one full discovery ingestion cycle across monitored sources."""
    if feeds is None:
        feeds = DEFAULT_FEEDS

    init_db(db_path)
    initial_count = get_source_count(db_path)
    total_new_items = 0
    total_feed_errors = 0

    logger.info(f"Starting ORBIT discovery cycle across {len(feeds)} sources...")

    existing_titles = get_recent_titles(limit=500, db_path=db_path)
    total_skipped_novelty = 0

    with RobustHttpClient() as client:
        for feed in feeds:
            feed_name = feed["name"]
            feed_url = feed["url"]
            is_html = feed.get("is_html", False)

            logger.info(f"Connecting to feed: [{feed_name}] -> {feed_url}")
            resp = client.get(feed_url)
            if not resp:
                logger.warning(f"Failed to fetch feed {feed_name}")
                total_feed_errors += 1
                continue

            # Parse feed items
            if is_html:
                items = extract_hn_links(resp.text)
            else:
                items = parse_feed_xml(resp.text, default_source_name=feed_name)

            logger.info(f"Found {len(items)} items from [{feed_name}]. Processing up to {max_items_per_feed}...")

            for item in items[:max_items_per_feed]:
                url = item["url"]
                title = item["title"]

                # Week 2 Novelty Filter: skip if cosine similarity to recent items >= 0.92
                novel, max_sim, match = is_novel(title, existing_titles, similarity_threshold=0.92)
                if not novel:
                    total_skipped_novelty += 1
                    logger.debug(f"  [-] Skipping non-novel item (sim={max_sim:.3f} to '{match}'): {title}")
                    continue

                published = item.get("published", "")
                summary = item.get("summary", "")
                raw_text = summary

                # Fetch full article text if requested and not an arXiv abs page (arXiv abstract is already in summary)
                if fetch_full_page and not ("arxiv.org" in url and "abs" in url):
                    try:
                        page_resp = client.get(url)
                        if page_resp and page_resp.status_code == 200:
                            page_title, page_text = clean_html(page_resp.text)
                            if page_text and len(page_text) > len(raw_text):
                                raw_text = page_text
                            if not title and page_title:
                                title = page_title
                    except Exception as e:
                        logger.debug(f"Could not extract full page for {url}: {e}")

                now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
                content_hash = compute_content_hash(f"{title} {raw_text[:1000]}")

                # Insert into DB
                row_id = insert_source(
                    url=url,
                    title=title,
                    published=published or now_iso,
                    raw_text=raw_text,
                    summary=summary or raw_text[:300],
                    fetched_at=now_iso,
                    source_name=feed_name,
                    content_hash=content_hash,
                    status="fetched",
                    db_path=db_path,
                )

                if row_id:
                    total_new_items += 1
                    existing_titles.append(title)
                    logger.info(f"  [+] Ingested ID={row_id}: {title[:75]}...")

    final_count = get_source_count(db_path)
    stats = {
        "new_items_ingested": total_new_items,
        "skipped_novelty": total_skipped_novelty,
        "feed_errors": total_feed_errors,
        "total_sources_in_db": final_count,
        "delta": final_count - initial_count,
    }
    logger.info(f"Discovery cycle complete: {stats}")
    return stats


def main():
    parser = argparse.ArgumentParser(description="ORBIT Discovery Collector")
    parser.add_argument("--once", action="store_true", help="Run a single collection pass and exit")
    parser.add_argument("--limit", type=int, default=10, help="Max items per source feed")
    parser.add_argument("--db", type=str, default="data/orbit.db", help="Path to SQLite database")
    args = parser.parse_args()

    if args.once or True:  # Default to running one pass
        run_collection_cycle(max_items_per_feed=args.limit, db_path=args.db)


if __name__ == "__main__":
    main()
