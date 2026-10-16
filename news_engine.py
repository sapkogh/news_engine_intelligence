import feedparser
import json
import time
import urllib.parse
import urllib.request
from urllib.request import Request, urlopen
from datetime import datetime, timezone
import html
import re

# Dictionary mapping country and source metadata to the standardized RSS endpoints
NEWS_FEEDS = {
    "Japan": {
        "source": "NHK World-Japan",
        "url": "https://www3.nhk.or.jp/rj/podcast/rss/english.xml"
    },
    "South Korea": {
        "source": "Yonhap News Agency",
        "url": "https://en.yna.co.kr/RSS/news.xml"
    },
    "China": {
        "source": "CGTN",
        "url": "https://www.cgtn.com/subscribe/rss/section/china.xml"
    },
    "United States": {
        "source": "NPR",
        "url": "https://feeds.npr.org/1001/rss.xml"
    },
    "Canada": {
        "source": "CBC News",
        "url": "https://rss.cbc.ca/lineup/world.xml"
    },
    "Mexico": {
        "source": "El Economista",
        "url": "https://www.eleconomista.com.mx/rss/ultimas-noticias"
    },
    "Germany": {
        "source": "Deutsche Welle",
        "url": "https://rss.dw.com/xml/rss-en-world"
    },
    "France": {
        "source": "France 24",
        "url": "https://www.france24.com/en/rss"
    },
    "Switzerland": {
        "source": "The Local Switzerland",
        "url": "https://feeds.thelocal.com/rss/ch"
    },
    "Italy": {
        "source": "ANSA English",
        "url": "https://www.ansa.it/sito/ansait_rss.xml"
    },
    "South Africa": {
        "source": "SABC News",
        "url": "https://www.sabcnews.com/sabcnews/feed/"
    },
    "Nigeria": {
        "source": "NAN",
        "url": "https://nannews.ng/feed/"
    },
    "Congo/Central Africa": {
        "source": "AllAfrica",
        "url": "https://allafrica.com/tools/headlines/rdf/centralafrica/headlines.rdf"
    },
    "Australia": {
        "source": "SBS News",
        "url": "https://www.sbs.com.au/news/topic/latest/feed"
    },
    "Global Baseline": {
        "source": "BBC News World",
        "url": "http://feeds.bbci.co.uk/news/world/rss.xml"
    }
}

# Thematic keyword lists for categorizing articles dynamically
CATEGORIES = {
    "Science": ["science", "space", "astronomy", "physics", "nasa", "evolution", "discovery", "planet"],
    "Technology": ["technology", "tech", "software", "ai", "artificial intelligence", "silicon", "semiconductor", "cyber", "chip", "quantum"],
    "Health": ["health", "medical", "virus", "vaccine", "medicine", "disease", "clinical", "fda", "pandemic", "outbreak", "biotech"]
}

def determine_category(title, summary):
    """Scans the title and text content to determine the focus sector."""
    combined_text = f"{title.lower()} {summary.lower()}"
    
    matched_categories = []
    for category, keywords in CATEGORIES.items():
        # Match whole words only, so "ai" does not match "said" or "Taiwan"
        if any(re.search(rf"\b{re.escape(keyword)}\b", combined_text) for keyword in keywords):
            matched_categories.append(category)
            
    # Default to Headline news if no specialized keywords match
    return matched_categories if matched_categories else ["Headline"]

def utc_now_str():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def safe_link(url):
    """Allow only http(s) links in the report; anything else becomes '#'."""
    url = (url or "").strip()
    return url if urllib.parse.urlsplit(url).scheme.lower() in ("http", "https") else "#"


def fetch_feed(country, info):
    """Fetch a feed with a browser-like user agent and bounded wait."""
    try:
        request = urllib.request.Request(
            info["url"],
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            parsed_data = feedparser.parse(response.read())
        if not parsed_data.entries:
            print(f"Warning: {country} ({info['source']}) returned no feed entries.")
        else:
            print(f"Successfully ingested {country} ({info['source']}) - Found {len(parsed_data.entries)} items.")
        return parsed_data
    except Exception as error:
        print(f"Warning: Failed to parse feed for {country}: {error}")
        return None

def clean_html(text):
    """Clean HTML content from summaries."""
    if not text:
        return ""
    # Remove HTML tags but preserve text content
    cleaned = html.unescape(text)
    # Remove any remaining HTML tags
    import re
    cleaned = re.sub(r'<[^>]+>', '', cleaned)
    # Clean up extra whitespace
    cleaned = ' '.join(cleaned.split())
    return cleaned

def get_full_content(entry):
    """Try to get full article content when possible."""
    # First try the summary field which may contain full content in some feeds
    if hasattr(entry, "summary") and entry.summary:
        return clean_html(entry.summary)
    
    # Try description field as fallback
    if hasattr(entry, "description") and entry.description:
        return clean_html(entry.description)
        
    # If no summary or description, use title as fallback but that's not ideal
    return ""

def parse_all_feeds(max_articles_per_feed=5):
    """Loops through all geopolitical feeds, cleans entries, and categorizes them."""
    aggregated_news = []
    
    print(f"=== Starting Global News Core Engine Intake Process ===")
    
    for country, meta in NEWS_FEEDS.items():
        print(f"Processing updates from: {country} ({meta['source']})...")
        try:
            feed = fetch_feed(country, meta)
            if feed is None:
                continue
            entries_processed = 0
            
            for entry in feed.entries:
                if entries_processed >= max_articles_per_feed:
                    break
                    
                title = getattr(entry, "title", "No Title Available")
                link = getattr(entry, "link", "#")
                summary = get_full_content(entry)
                published = getattr(entry, "published", utc_now_str())
                
                # Assign thematic tags programmatically
                tags = determine_category(title, summary)
                
                article_data = {
                    "country": country,
                    "source": meta["source"],
                    "title": title,
                    "link": link,
                    "summary": summary,
                    "published_raw": published,
                    "categories": tags,
                    "processed_at": utc_now_str()
                }
                
                aggregated_news.append(article_data)
                entries_processed += 1
                
        except Exception as e:
            print(f"[Error parsing feed for {country}]: {e}")
            continue
            
    print(f"\n=== Pipeline Finished. Successfully parsed {len(aggregated_news)} global tracking entries. ===\n")
    return aggregated_news

def generate_html_report(articles, output_path="global_news_manifest.html"):
    """Render the collected articles as a standalone HTML report."""
    source_options = sorted({article["source"] for article in articles})
    filter_options = "\n".join(
        f'                    <option value="{html.escape(source)}">{html.escape(source)}</option>'
        for source in source_options
    )
    article_cards = []
    for article in articles:
        categories = " ".join(
            f'<span class="tag">{html.escape(category)}</span>'
            for category in article.get("categories", [])
        )
        article_cards.append(f"""
            <article class="story" data-source="{html.escape(article.get('source', ''))}">
                <div class="story-meta">
                    <span>{html.escape(article.get('country', 'Unknown'))}</span>
                    <span>{html.escape(article.get('source', 'Unknown source'))}</span>
                </div>
                <h2><a href="{html.escape(safe_link(article.get('link')))}" target="_blank" rel="noopener noreferrer">{html.escape(article.get('title', 'Untitled'))}</a></h2>
                <p>{html.escape(article.get('summary', 'No summary available'))}</p>
                <div class="story-footer">
                    <time>{html.escape(article.get('published_raw', 'Date unavailable'))}</time>
                    <div>{categories}</div>
                </div>
            </article>
        """)

    report = f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Global News Intelligence</title>
    <style>
        :root {{
            --ink: #17212b;
            --muted: #66727d;
            --line: #d8e0e6;
            --paper: #f4f6f7;
            --accent: #c94b32;
            --accent-dark: #8e2f20;
        }}
        * {{ box-sizing: border-box; }}
        body {{ margin: 0; color: var(--ink); background: var(--paper); font: 16px/1.55 Georgia, serif; }}
        header {{ padding: 48px max(24px, calc((100% - 1180px) / 2)); color: #fff; background: #17212b; border-bottom: 6px solid var(--accent); }}
        header p {{ margin: 8px 0 0; color: #c8d1d8; font: 15px/1.4 Arial, sans-serif; }}
        h1 {{ margin: 0; font-size: clamp(2rem, 5vw, 4.5rem); line-height: .98; letter-spacing: 0; }}
        main {{ max-width: 1180px; margin: 0 auto; padding: 28px 24px 64px; }}
        .toolbar {{ display: flex; flex-wrap: wrap; align-items: center; gap: 12px; margin-bottom: 24px; font-family: Arial, sans-serif; }}
        .count {{ margin-right: auto; color: var(--muted); font-size: 14px; }}
        select {{ min-width: 220px; padding: 11px 12px; color: var(--ink); background: #fff; border: 1px solid var(--line); border-radius: 4px; font: inherit; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(290px, 1fr)); gap: 18px; }}
        .story {{ display: flex; flex-direction: column; min-height: 280px; padding: 22px; background: #fff; border: 1px solid var(--line); border-top: 4px solid var(--accent); box-shadow: 0 5px 16px rgba(23, 33, 43, .06); }}
        .story-meta, .story-footer {{ display: flex; justify-content: space-between; gap: 12px; color: var(--muted); font: 12px/1.35 Arial, sans-serif; }}
        .story-meta span:last-child {{ color: var(--accent-dark); font-weight: 700; text-align: right; }}
        h2 {{ margin: 14px 0 10px; font-size: 1.35rem; line-height: 1.15; }}
        h2 a {{ color: var(--ink); text-decoration: none; }}
        h2 a:hover {{ color: var(--accent); }}
        .story p {{ flex: 1; margin: 0 0 20px; color: #46515b; font-size: .98rem; }}
        .story-footer {{ align-items: end; padding-top: 15px; border-top: 1px solid var(--line); }}
        .tag {{ display: inline-block; margin: 0 0 0 5px; padding: 3px 7px; color: var(--accent-dark); background: #f9e5df; border-radius: 12px; font-size: 11px; }}
        .empty {{ padding: 40px; color: var(--muted); text-align: center; background: #fff; }}
        @media (max-width: 600px) {{ header {{ padding: 34px 20px; }} main {{ padding: 22px 16px 48px; }} .story-meta, .story-footer {{ align-items: flex-start; flex-direction: column; }} .story-meta span:last-child {{ text-align: left; }} }}
    </style>
</head>
<body>
    <header>
        <h1>Global News Intelligence</h1>
        <p>{len(articles)} stories collected from {len(source_options)} sources</p>
    </header>
    <main>
        <div class="toolbar">
            <span class="count" id="visible-count">Showing {len(articles)} stories</span>
            <label for="source-filter">Filter by source</label>
            <select id="source-filter">
                <option value="all">All sources</option>
{filter_options}
            </select>
        </div>
        <section class="grid" id="story-grid">
{''.join(article_cards) if article_cards else '<div class="empty">No news articles were collected.</div>'}
        </section>
    </main>
    <script>
        const filter = document.getElementById('source-filter');
        const stories = [...document.querySelectorAll('.story')];
        const count = document.getElementById('visible-count');
        filter.addEventListener('change', () => {{
            const selected = filter.value;
            let visible = 0;
            stories.forEach((story) => {{
                const show = selected === 'all' || story.dataset.source === selected;
                story.hidden = !show;
                if (show) visible += 1;
            }});
            count.textContent = `Showing ${{visible}} stories`;
        }});
    </script>
</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(report)
    print(f"Dev Environment Update: HTML report saved locally to '{output_path}'.")

if __name__ == "__main__":
    # Test sample pipeline run
    processed_data = parse_all_feeds(max_articles_per_feed=3)
    
    # Save a local JSON blueprint representing what will eventually stream into your database
    output_path = "global_news_manifest.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(processed_data, f, indent=4, ensure_ascii=False)
    print(f"Dev Environment Update: Structured raw data saved locally to '{output_path}'.")
    generate_html_report(processed_data)
