# Global News Intelligence Engine

Fetches articles from configured RSS feeds and generates:

- `global_news_manifest.json` - structured article data
- `global_news_manifest.html` - a filterable browser report

## Requirements

- Python 3.9 or newer
- Internet access

## Setup

Clone the repository and open its folder:

```powershell
git clone https://github.com/sapkogh/news_engine_intelligence.git
cd news_engine_intelligence
```

Install the Python dependency:

```powershell
python -m pip install feedparser
```

On Windows, use `py` if `python` is not available:

```powershell
py -m pip install feedparser
```

## Generate the report

Run the engine:

```powershell
python news_engine.py
```

This fetches the configured feeds and overwrites both output files:

- `global_news_manifest.json`
- `global_news_manifest.html`

The engine keeps up to three articles per feed by default. Feed availability depends on the publisher and the user's network.

## View the HTML report

Start a local web server from the repository folder:

```powershell
python -m http.server 8000
```

Open this address in a browser:

```text
http://localhost:8000/global_news_manifest.html
```

Keep the terminal running while viewing the report. Press `Ctrl+C` in the terminal to stop the server.

## Configure feeds

Edit `NEWS_FEEDS` in `news_engine.py` to add or change a source. Each source must point to an RSS or Atom feed URL, not just the publisher homepage.

Some publishers may block automated requests, remove feeds, or return no articles. The engine reports those cases and continues with the remaining sources.
