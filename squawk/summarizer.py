import time
import feedparser
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any
from .sentiment import sentiment_score


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


def score_and_rank(items: List[Dict], pos_extra=None, neg_extra=None, top=10) -> Dict:
    scored = []
    for it in items:
        score, label = sentiment_score(
            f"{it['title']} {it['summary']}", pos_extra, neg_extra
        )
        it["score"] = score
        it["label"] = label
        scored.append(it)

    scored.sort(
        key=lambda x: (abs(x["score"]), x["ts"] or time.gmtime(0)), reverse=True
    )
    top_items = scored[:top]

    if not top_items:
        overall_label = "neutral"
        avg = 0.0
        counts = {"risk-on": 0, "neutral": 0, "risk-off": 0}
    else:
        avg = sum(i["score"] for i in top_items) / len(top_items)
        counts = {
            "risk-on": sum(1 for i in top_items if i["label"] == "risk-on"),
            "neutral": sum(1 for i in top_items if i["label"] == "neutral"),
            "risk-off": sum(1 for i in top_items if i["label"] == "risk-off"),
        }
        overall_label = (
            "risk-on" if avg > 0.3 else "risk-off" if avg < -0.3 else "neutral"
        )

    return {
        "items": top_items,
        "average_score": avg,
        "overall_label": overall_label,
        "counts": counts,
    }
