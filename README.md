# UK COVID-19 Twitter Sentiment Dashboard

A **fully static** interactive dashboard analyzing ~300,000 UK tweets about COVID-19 and lockdown from **20 March 2020 to 25 March 2021**. Explore how sentiment shifted across UK counties in response to key events, cases, and deaths — compared across four NLP techniques.

No server. No backend. No build step at deploy time. Just HTML, CSS, JS, and pre-computed JSON.

---

## Features

- **Interactive timeline** — drag the slider across 371 days, or hit Play to animate sentiment evolution day-by-day
- **County-level choropleth** — UK map colored by average sentiment, updating live as the date changes
- **Four NLP techniques side-by-side** — Vader, TextBlob, LSTM, Naive Bayes
- **Two tweet datasets** — tweets mentioning *covid/coronavirus/covid-19* or *lockdown*
- **Daily context** — cumulative cases, deaths, R-number, top 10 hashtags, top emojis, and Guardian news headlines for every date
- **7-day moving averages** — smoothed sentiment and COVID stats per country (England, Scotland, Wales, Northern Ireland)
- **Analysis views** — notable days table, sentiment-vs-volume subplots, technique comparison, correlation matrix, wordclouds
- **Responsive** — scales from 4K desktop down to small phones; debounced chart re-render on viewport changes

## Tech Stack

| Layer | Technology |
|---|---|
| Rendering | Vanilla JS + [Plotly.js](https://plotly.com/javascript/) (via CDN) |
| Typography | [DM Mono](https://fonts.google.com/specimen/DM+Mono) + [Newsreader](https://fonts.google.com/specimen/Newsreader) (via Google Fonts) |
| Styling | Hand-written CSS — warm-parchment design system with dot-grid and noise textures |
| Data pipeline | Python + pandas (offline build step only) |
| Hosting | Any static host — GitHub Pages, Netlify, Vercel static, S3+CloudFront, etc. |

## Project Structure

```
covid-sentiment-nlp-uk/
├── index.html           # Single-page app entry point
├── css/style.css        # Design system + responsive layout
├── js/app.js            # Data loading + Plotly chart builders + UI
├── assets/              # Wordcloud images and favicon
├── build.py             # One-time data pre-computation script
└── data/
    ├── covid/           # COVID tweet CSVs (source)
    ├── covid-data/      # COVID statistics (source)
    ├── events/          # Key events + Guardian news (source)
    ├── geojson/         # UK counties GeoJSON (source)
    ├── lockdown/        # Lockdown tweet CSVs (source)
    └── json/            # Pre-computed output (committed, ~9.5 MB)
```

## Running Locally

The site must be served over HTTP (not `file://`) because it uses `fetch()` for JSON.

```bash
python3 -m http.server 8000
```

Then open **http://localhost:8000**.

Initial page load fetches ~7 MB of JSON (county sentiment + sentiment counts are the largest) — charts appear within 1–2 seconds on a typical connection.

## Regenerating the JSON

The pre-computed JSON in `data/json/` is already committed, so you don't need to run anything to view the dashboard. To regenerate it after changing source CSVs:

```bash
python3 -m venv venv
source venv/bin/activate
pip install pandas numpy
python3 build.py
```

**What the build script does:**

- Reads 49 MB of source CSVs
- Pre-aggregates the 40 MB of raw tweet-level sentiment into ~520 KB of per-date counts (`{date: {nlp: {country: {neg,neu,pos}}}}`) — raw tweets are never shipped to the client
- Pre-computes all 7-day moving averages for sentiment, tweet volume, and COVID stats
- Parses hashtag tuple strings into clean JSON
- Normalizes event dates to ISO format and filters to the dashboard date range
- Writes ~9.5 MB of optimized JSON to `data/json/`

All the heavy pandas lifting happens once at build time — the client only does array filtering and Plotly rendering.

## Deploying

Upload the repo root to any static host:

| Host | Steps |
|---|---|
| **GitHub Pages** | Enable Pages in repo settings → deploy from `main` branch, root folder |
| **Netlify** | Connect the repo, no build command, publish directory = `/` |
| **Vercel** | Connect the repo as a static project, no framework preset needed |
| **Cloudflare Pages / S3 / any CDN** | Upload everything except the `venv/` directory |

No CI build step required — the JSON is committed.

## Data Sources

- **Twitter data** — scraped with [SNScrape](https://github.com/JustAnotherArchivist/snscrape), keywords: `coronavirus OR covid OR covid19 OR covid-19` and `lockdown`. See [Twitter Developer Policy](https://developer.twitter.com/en/developer-terms/agreement-and-policy).
- **COVID statistics** — [Public Health England](https://coronavirus.data.gov.uk/)
- **News events** — [Guardian News API](https://open-platform.theguardian.com/)
- **Geographic data** — UK ceremonial counties GeoJSON

## Sentiment Techniques

Each tweet is scored by four independent methods. The dashboard lets you switch between them to compare:

- **[Vader](https://github.com/cjhutto/vaderSentiment)** — lexicon + rules, tuned for social media
- **[TextBlob](https://github.com/sloria/TextBlob)** — Pattern-based, averaged polarity
- **LSTM** — trained neural network on labeled tweet sentiment (see [reference paper](https://www.aclweb.org/anthology/O18-1021.pdf))
- **[Naive Bayes](https://web.stanford.edu/~jurafsky/slp3/4.pdf)** — classic probabilistic classifier

All methods emit scores in `[-1, 1]` and categorical predictions `(neg, neu, pos)`.

## License

MIT — see LICENSE file.
