"""Self-contained verification suite for ORBIT collector and storage."""

import os
import tempfile
from src.knowledge.db import init_db, insert_source, get_source_count, get_latest_sources
from src.discovery.feed_parser import parse_feed_xml
from src.extraction.extractor import clean_html, compute_content_hash
from src.discovery.http_client import RobustHttpClient

def test_db_storage_and_deduplication():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_db = f.name
    try:
        init_db(temp_db)
        assert get_source_count(temp_db) == 0

        # Insert first record
        hash1 = compute_content_hash("Emerging Solid-State Battery Tech")
        id1 = insert_source(
            url="https://example.com/battery-1",
            title="Breakthrough in Solid-State Electrolytes",
            published="2026-10-17T00:00:00Z",
            raw_text="Researchers at MIT have demonstrated high ionic conductivity.",
            summary="Solid-state breakthrough.",
            fetched_at="2026-10-17T00:00:00Z",
            source_name="MIT News",
            content_hash=hash1,
            db_path=temp_db,
        )
        assert id1 is not None
        assert get_source_count(temp_db) == 1

        # Attempt to insert same URL (should be rejected)
        id2 = insert_source(
            url="https://example.com/battery-1",
            title="Duplicate Title",
            published="2026-10-17T01:00:00Z",
            raw_text="Different text.",
            summary="Dupe",
            fetched_at="2026-10-17T01:00:00Z",
            source_name="Other Source",
            content_hash=compute_content_hash("Different text"),
            db_path=temp_db,
        )
        assert id2 is None, "Duplicate URL must be rejected"
        assert get_source_count(temp_db) == 1

        # Attempt to insert same content hash with different URL (reprint detection)
        id3 = insert_source(
            url="https://syndicated.com/mirror",
            title="Copied Title",
            published="2026-10-17T02:00:00Z",
            raw_text="Emerging Solid-State Battery Tech",
            summary="Copied summary",
            fetched_at="2026-10-17T02:00:00Z",
            source_name="Syndicator",
            content_hash=hash1,
            db_path=temp_db,
        )
        assert id3 is None, "Duplicate content hash must be rejected"
        assert get_source_count(temp_db) == 1

        latest = get_latest_sources(limit=5, db_path=temp_db)
        assert len(latest) == 1
        assert latest[0]["title"] == "Breakthrough in Solid-State Electrolytes"
    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)


def test_rss_and_atom_parser():
    sample_rss = """
    <rss version="2.0">
        <channel>
            <title>Test Science Feed</title>
            <item>
                <title>New Quantum Memory Record</title>
                <link>https://arxiv.org/abs/2610.12345</link>
                <pubDate>Sat, 17 Oct 2026 12:00:00 GMT</pubDate>
                <description>&lt;p&gt;Coherence time extended by 10x.&lt;/p&gt;</description>
            </item>
        </channel>
    </rss>
    """
    items = parse_feed_xml(sample_rss, default_source_name="Test RSS")
    assert len(items) == 1
    assert items[0]["title"] == "New Quantum Memory Record"
    assert items[0]["url"] == "https://arxiv.org/abs/2610.12345"
    assert "Coherence time extended" in items[0]["summary"]

    sample_atom = """
    <feed xmlns="http://www.w3.org/2005/Atom">
        <title>Atom AI Feed</title>
        <entry>
            <title>Autonomous Tool-Using Agents</title>
            <link href="https://example.org/atom-agent" rel="alternate"/>
            <updated>2026-10-17T10:00:00Z</updated>
            <summary>Agents operating software interfaces.</summary>
        </entry>
    </feed>
    """
    atom_items = parse_feed_xml(sample_atom, default_source_name="Atom Feed")
    assert len(atom_items) == 1
    assert atom_items[0]["title"] == "Autonomous Tool-Using Agents"
    assert atom_items[0]["url"] == "https://example.org/atom-agent"


def test_clean_html_extractor():
    sample_html = """
    <!DOCTYPE html>
    <html>
        <head><title>Superconducting Circuit Breakthrough</title></head>
        <body>
            <header><nav><a href="/">Home</a></nav></header>
            <article>
                <h1>Room-temperature Superconductor Replication</h1>
                <p>Researchers verified the crystal structure under ambient pressures.</p>
                <script>console.log("ad code");</script>
            </article>
            <footer>Copyright 2026</footer>
        </body>
    </html>
    """
    title, text = clean_html(sample_html)
    assert title == "Superconducting Circuit Breakthrough"
    assert "Room-temperature Superconductor Replication" in text
    assert "Researchers verified the crystal structure" in text
    assert "console.log" not in text
    assert "Copyright" not in text


if __name__ == "__main__":
    print("Running ORBIT Week 1 verification checks...")
    test_db_storage_and_deduplication()
    print("  [x] DB storage and URL/hash deduplication verified")
    test_rss_and_atom_parser()
    print("  [x] RSS and Atom parsers verified")
    test_clean_html_extractor()
    print("  [x] HTML extractor and cleaner verified")
    print("\nALL ORBIT WEEK 1 CHECKS PASSED SUCCESSFULLY!")
