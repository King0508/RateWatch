import os
import argparse
import yaml
import requests
from .summarizer import fetch_items, within_hours, filter_keywords, score_and_rank
from .formatting import format_markdown, format_slack


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
        print("[warn] SLACK_WEBHOOK_URL not set; skipping Slack push.")
        return
    resp = requests.post(hook, json={"text": text}, timeout=10)
    if resp.status_code >= 300:
        print(f"[warn] Slack webhook failed: {resp.status_code} {resp.text[:200]}")


def main():
    ap = argparse.ArgumentParser(description="Fixed-Income News Summarizer (Squawk)")
    ap.add_argument("--config", default="config.yaml", help="Path to YAML config")
    ap.add_argument("--hours", type=int, default=12, help="Lookback window in hours")
    ap.add_argument("--top", type=int, default=10, help="Top N items to show")
    ap.add_argument(
        "--push", choices=["none", "slack"], default="none", help="Optional push target"
    )
    args = ap.parse_args()

    cfg = load_config(args.config)

    print("[info] Fetching feeds...")
    items = fetch_items(cfg["feeds"])
    print(f"[info] pulled {len(items)} items")

    items = within_hours(items, args.hours)
    print(f"[info] within last {args.hours}h: {len(items)}")

    items = filter_keywords(items, cfg["keywords"]["must_have_any"], cfg["stop_words"])
    print(f"[info] after keyword filter: {len(items)}")

    report = score_and_rank(
        items,
        pos_extra=cfg["sentiment_overrides"]["positive"],
        neg_extra=cfg["sentiment_overrides"]["negative"],
        top=args.top,
    )

    md = format_markdown(report)
    print(md)

    if args.push == "slack" and report["items"]:
        text = format_slack(report)
        push_slack(text)


if __name__ == "__main__":
    main()
