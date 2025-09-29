from datetime import datetime, timezone
from typing import Dict


def format_markdown(report: Dict) -> str:
    dt = datetime.now(timezone.utc).astimezone()
    header = f"# Fixed-Income Squawk — {dt.strftime('%Y-%m-%d %H:%M %Z')}\n"
    mood = f"**Desk Mood:** {report['overall_label']}  (avg score: {report['average_score']:+.2f})\n\n"
    counts = f"**Counts:** risk-on {report['counts']['risk-on']}, neutral {report['counts']['neutral']}, risk-off {report['counts']['risk-off']}\n"
    lines = [header, mood, counts, "\n---\n"]

    for i, item in enumerate(report["items"], 1):
        t = item["published_local"]
        lines.append(
            f"**{i}. {item['title']}**  \n"
            f"{t} | {item['source']} | {item['label']} (score {item['score']:+d})  \n"
            f"{item['summary']}  \n"
            f"[link]({item['link']})\n"
        )
    return "\n".join(lines)


def format_slack(report: Dict) -> str:
    head = f"*Fixed-Income Squawk* — *{report['overall_label']}* (avg {report['average_score']:+.2f})"
    lines = [head]
    for item in report["items"]:
        lines.append(
            f"• {item['label']}: *{item['title']}* — {item['source']} [{item['published_local']}]"
        )
        lines.append(f"  {item['link']}")
    return "\n".join(lines)
