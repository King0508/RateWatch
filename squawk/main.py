import os
import argparse
import yaml
import requests
import logging
from datetime import datetime, timezone
from .summarizer import fetch_items, within_hours, filter_keywords, score_and_rank
from .formatting import format_markdown, format_slack

# Import new ML components
try:
    from .ml_sentiment import sentiment_score_ml
    from .entity_extraction import extract_entities

    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

# Import warehouse integration
try:
    from .warehouse_integration import get_warehouse

    WAREHOUSE_AVAILABLE = True
except ImportError:
    WAREHOUSE_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg.setdefault("feeds", [])
    cfg.setdefault("keywords", {}).setdefault("must_have_any", [])
    cfg.setdefault("stop_words", [])
    cfg.setdefault("sentiment_overrides", {}).setdefault("positive", [])
    cfg["sentiment_overrides"].setdefault("negative", [])
    return cfg


def push_slack(text: str) -> None:
    hook = os.getenv("SLACK_WEBHOOK_URL")
    if not hook:
        logger.warning("SLACK_WEBHOOK_URL not set; skipping Slack push.")
        return
    resp = requests.post(hook, json={"text": text}, timeout=10)
    if resp.status_code >= 300:
        logger.warning(f"Slack webhook failed: {resp.status_code} {resp.text[:200]}")


def process_with_ml(items: list, use_ml: bool = True) -> list:
    """
    Process items with ML sentiment analysis and entity extraction.

    Args:
        items: List of news items
        use_ml: Whether to use ML models (default: True)

    Returns:
        Items with added sentiment_score, sentiment_label, confidence, entities
    """
    if not use_ml or not ML_AVAILABLE:
        logger.info("ML processing disabled or unavailable, using rule-based sentiment")
        return items

    logger.info("Processing items with FinBERT and entity extraction...")

    for item in items:
        text = f"{item['title']} {item['summary']}"

        # ML sentiment analysis
        try:
            score, label, confidence = sentiment_score_ml(text)
            item["sentiment_score"] = score
            item["sentiment_label"] = label
            item["confidence"] = confidence
        except Exception as e:
            logger.warning(f"ML sentiment failed: {e}, using fallback")
            # Fallback to rule-based
            item["sentiment_score"] = item.get("score", 0)
            item["sentiment_label"] = item.get("label", "neutral")
            item["confidence"] = 0.5

        # Entity extraction
        try:
            entities = extract_entities(text)
            item["entities"] = entities
        except Exception as e:
            logger.warning(f"Entity extraction failed: {e}")
            item["entities"] = {}

        # Add timestamp if missing
        if "timestamp" not in item or item["timestamp"] is None:
            item["timestamp"] = datetime.now(timezone.utc)

    return items


def store_in_warehouse(items: list, warehouse_path: str = None) -> bool:
    """
    Store processed items in DuckDB warehouse.

    Args:
        items: Processed news items with sentiment
        warehouse_path: Optional path to warehouse database

    Returns:
        True if successful, False otherwise
    """
    if not WAREHOUSE_AVAILABLE:
        logger.warning("Warehouse integration not available")
        return False

    try:
        logger.info("Storing items in warehouse...")
        warehouse = get_warehouse(warehouse_path)

        # Bulk insert news items
        count = warehouse.bulk_insert_news(items)
        logger.info(f"Stored {count} items in warehouse")

        # Compute hourly aggregates
        agg_count = warehouse.compute_sentiment_aggregates(hours_back=24)
        logger.info(f"Computed {agg_count} sentiment aggregates")

        # Show stats
        stats = warehouse.get_stats()
        logger.info(f"Warehouse stats: {stats}")

        return True

    except Exception as e:
        logger.error(f"Failed to store in warehouse: {e}")
        return False


def main():
    ap = argparse.ArgumentParser(
        description="Fixed-Income News Summarizer with ML Sentiment Analysis"
    )
    ap.add_argument("--config", default="config.yaml", help="Path to YAML config")
    ap.add_argument("--hours", type=int, default=12, help="Lookback window in hours")
    ap.add_argument("--top", type=int, default=10, help="Top N items to show")
    ap.add_argument(
        "--push", choices=["none", "slack"], default="none", help="Optional push target"
    )
    ap.add_argument(
        "--no-ml", action="store_true", help="Disable ML sentiment (use rule-based)"
    )
    ap.add_argument(
        "--no-warehouse", action="store_true", help="Disable warehouse storage"
    )
    ap.add_argument(
        "--warehouse-path", type=str, default=None, help="Path to warehouse.duckdb"
    )
    args = ap.parse_args()

    cfg = load_config(args.config)

    logger.info("Fetching feeds...")
    items = fetch_items(cfg["feeds"])
    logger.info(f"Pulled {len(items)} items")

    items = within_hours(items, args.hours)
    logger.info(f"Within last {args.hours}h: {len(items)}")

    items = filter_keywords(items, cfg["keywords"]["must_have_any"], cfg["stop_words"])
    logger.info(f"After keyword filter: {len(items)}")

    # Process with ML if enabled
    use_ml = not args.no_ml and ML_AVAILABLE
    if use_ml:
        items = process_with_ml(items, use_ml=True)
        logger.info("ML processing complete")
    else:
        # Use rule-based sentiment as fallback
        report = score_and_rank(
            items,
            pos_extra=cfg["sentiment_overrides"]["positive"],
            neg_extra=cfg["sentiment_overrides"]["negative"],
            top=args.top,
        )
        items = report["items"]

        # Normalize field names for warehouse compatibility
        for item in items:
            if "score" in item and "sentiment_score" not in item:
                item["sentiment_score"] = item["score"]
            if "label" in item and "sentiment_label" not in item:
                item["sentiment_label"] = item["label"]
            if "sentiment_label" not in item:
                item["sentiment_label"] = "neutral"
            if "sentiment_score" not in item:
                item["sentiment_score"] = 0.0
            # Convert timestamp
            if "ts" in item and "timestamp" not in item:
                import time
                from datetime import datetime, timezone

                dt = datetime.fromtimestamp(time.mktime(item["ts"]), tz=timezone.utc)
                item["timestamp"] = dt
            # Add missing fields with defaults
            if "confidence" not in item:
                item["confidence"] = 0.75  # Default confidence for rule-based
            if "entities" not in item:
                item["entities"] = {}

    # Store in warehouse if enabled
    if not args.no_warehouse and WAREHOUSE_AVAILABLE:
        store_in_warehouse(items, args.warehouse_path)

    # Sort by sentiment score for display
    items_sorted = sorted(
        items, key=lambda x: abs(x.get("sentiment_score", 0)), reverse=True
    )
    top_items = items_sorted[: args.top]

    # Format for display
    report = {
        "items": top_items,
        "average_score": (
            sum(i.get("sentiment_score", 0) for i in top_items) / len(top_items)
            if top_items
            else 0
        ),
        "overall_label": (
            "risk-on"
            if sum(i.get("sentiment_score", 0) for i in top_items) > 0
            else (
                "risk-off"
                if sum(i.get("sentiment_score", 0) for i in top_items) < 0
                else "neutral"
            )
        ),
        "counts": {
            "risk-on": sum(
                1 for i in top_items if i.get("sentiment_label") == "risk-on"
            ),
            "risk-off": sum(
                1 for i in top_items if i.get("sentiment_label") == "risk-off"
            ),
            "neutral": sum(
                1 for i in top_items if i.get("sentiment_label") == "neutral"
            ),
        },
    }

    md = format_markdown(report)
    print(md)

    if args.push == "slack" and report["items"]:
        text = format_slack(report)
        push_slack(text)

    logger.info("Processing complete!")


if __name__ == "__main__":
    main()
