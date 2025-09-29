# Fixed-Income News Summarizer ("Squawk")

Pulls market/econ headlines from RSS, filters for fixed-income topics (rates, inflation, credit),
tags basic sentiment (risk-on / risk-off / neutral), and prints a one-page summary.
Optionally pushes top headlines to Slack.

## Quickstart

```bash
python -m venv .venv
# Win: .venv\Scripts\activate | macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m squawk.main --config config.yaml --hours 12 --top 10
```
