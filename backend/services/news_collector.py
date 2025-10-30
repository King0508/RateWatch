import time
import feedparser
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


def _to_dt_struct(entry) -> time.struct_time | None:
    for key in ("published_parsed", "updated_parsed"):
        val = getattr(entry, key, None) or (
            entry.get(key) if isinstance(entry, dict) else None
        )
        if val:
            return val
    return None


def _to_local_iso(ts: time.struct_time | None) -> str:
    if not ts:
        return "n/a"
    dt = datetime.fromtimestamp(time.mktime(ts), tz=timezone.utc).astimezone()
    return dt.strftime("%Y-%m-%d %H:%M")


def fetch_items(feed_urls: List[str]) -> List[Dict[str, Any]]:
    items = []
    for url in feed_urls:
        parsed = feedparser.parse(url)
        source = parsed.feed.get("title", url)
        for e in parsed.entries:
            title = e.get("title", "").strip()
            summary = e.get("summary", "").strip()
            link = e.get("link", "").strip()
            ts = _to_dt_struct(e)
            items.append(
                {
                    "source": source,
                    "title": title,
                    "summary": summary,
                    "link": link,
                    "ts": ts,
                    "published_local": _to_local_iso(ts),
                    "raw": e,
                }
            )
    return items


def within_hours(items: List[Dict], hours: int) -> List[Dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    out = []
    for it in items:
        if not it["ts"]:
            continue
        dt = datetime.fromtimestamp(time.mktime(it["ts"]), tz=timezone.utc)
        if dt >= cutoff:
            out.append(it)
    return out


def filter_keywords(
    items: List[Dict], must_any: List[str], stop_words: List[str]
) -> List[Dict]:
    must_any_l = [w.lower() for w in must_any]
    stop_l = [w.lower() for w in stop_words]
    out = []
    for it in items:
        hay = f"{it['title']} {it['summary']}".lower()
        if any(sw in hay for sw in stop_l):
            continue
        if not must_any_l or any(kw in hay for kw in must_any_l):
            out.append(it)
    return out


class NewsCollector:
    """
    Collects and filters news from RSS feeds.
    """
    
    def __init__(self, feed_urls: List[str], keywords: List[str], stop_words: List[str]):
        self.feed_urls = feed_urls
        self.keywords = keywords
        self.stop_words = stop_words
    
    def collect_news(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Collect and filter news from configured feeds.
        
        Args:
            hours: How many hours back to collect news
            
        Returns:
            List of filtered news items
        """
        logger.info(f"Fetching news from {len(self.feed_urls)} feeds...")
        items = fetch_items(self.feed_urls)
        logger.info(f"Fetched {len(items)} total items")
        
        items = within_hours(items, hours)
        logger.info(f"Found {len(items)} items within last {hours} hours")
        
        items = filter_keywords(items, self.keywords, self.stop_words)
        logger.info(f"Filtered to {len(items)} relevant items")
        
        return items
