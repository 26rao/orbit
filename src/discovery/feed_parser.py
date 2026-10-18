"""Resilient RSS 2.0 and Atom feed parser using standard library xml.etree."""

import xml.etree.ElementTree as ET
import re
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def parse_feed_xml(xml_content: str, default_source_name: str = "Unknown") -> List[Dict[str, Any]]:
    """
    Parse RSS 2.0 or Atom XML content into a normalized list of feed items.
    Strips XML namespaces to cleanly and uniformly parse RSS, RDF, and Atom feeds.
    Each item dict contains: title, url, published, summary, source_name.
    """
    if not xml_content or not xml_content.strip():
        return []

    # Strip XML declaration, namespace declarations, and tag prefixes (e.g., dc:creator -> creator)
    content_no_decl = re.sub(r"<\?xml.*?\?>", "", xml_content.strip())
    content_no_ns = re.sub(r'\sxmlns(?::\w+)?="[^"]*"', "", content_no_decl)
    content_clean = re.sub(r"<(/?)[a-zA-Z0-9_-]+:([a-zA-Z0-9_-]+)", r"<\1\2", content_no_ns)

    try:
        root = ET.fromstring(content_clean)
    except ET.ParseError as e:
        logger.warning(f"XML parse error: {e}. Trying raw fallback.")
        try:
            root = ET.fromstring(xml_content.encode("utf-8", errors="replace"))
        except Exception as e2:
            logger.error(f"Failed to parse XML: {e2}")
            return []

    items = []

    # 1. RSS / RDF format: channel -> item
    channel = root.find(".//channel") or root.find("channel")
    channel_title = default_source_name
    if channel is not None:
        title_tag = channel.find("title")
        if title_tag is not None and title_tag.text:
            channel_title = title_tag.text.strip()

        for item in root.findall(".//item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            pub_date = (item.findtext("pubDate") or item.findtext("date") or "").strip()
            description = (item.findtext("description") or "").strip()
            clean_desc = re.sub(r"<[^>]+>", "", description).strip()

            if link and title:
                items.append({
                    "title": title,
                    "url": link,
                    "published": pub_date,
                    "summary": clean_desc[:500],
                    "source_name": channel_title,
                })
        if items:
            return items

    # 2. Atom format: feed -> entry
    feed_title_tag = root.find("title")
    if feed_title_tag is not None and feed_title_tag.text:
        channel_title = feed_title_tag.text.strip()

    for entry in root.findall(".//entry"):
        title = (entry.findtext("title") or "").strip()

        # Link resolution
        link = ""
        for link_el in entry.findall("link"):
            rel = link_el.attrib.get("rel")
            if rel in ("alternate", None) and "href" in link_el.attrib:
                link = link_el.attrib["href"]
                break
        if not link:
            link_el = entry.find("link")
            if link_el is not None and "href" in link_el.attrib:
                link = link_el.attrib["href"]
            elif link_el is not None and link_el.text:
                link = link_el.text.strip()

        published = (
            entry.findtext("published")
            or entry.findtext("updated")
            or entry.findtext("date")
            or ""
        ).strip()

        summary = (
            entry.findtext("summary")
            or entry.findtext("content")
            or ""
        ).strip()
        clean_summary = re.sub(r"<[^>]+>", "", summary).strip()

        if link and title:
            items.append({
                "title": title,
                "url": link,
                "published": published,
                "summary": clean_summary[:500],
                "source_name": channel_title,
            })

    return items
