#!/usr/bin/env python3
"""
Build script for COVID-19 Sentiment Dashboard.
Reads source CSV data and generates optimized JSON files for the static frontend.
Run: python build.py
"""

import json
import re
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
SOURCE_DIR = BASE_DIR / 'data'
OUTPUT_DIR = BASE_DIR / 'data' / 'json'

START_DATE = '2020-03-20'
END_DATE = '2021-03-25'
MA_WINDOW = 7
COUNTRIES = ['England', 'Scotland', 'Northern Ireland', 'Wales']
NLP_TYPES = ['nn', 'vader', 'textblob', 'native']
SCORE_AVG_COLS = ['nn-score_avg', 'textblob-score_avg', 'vader-score_avg', 'native-score_avg']
SCORE_COLS = {'nn': 'nn-score', 'textblob': 'textblob-score', 'vader': 'vader-score', 'native': 'native-score'}
PREDICTION_COLS = {'nn': 'nn-predictions', 'vader': 'vader-predictions',
                   'textblob': 'textblob-predictions', 'native': 'native-predictions'}
TOPICS = ['covid', 'lockdown']


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        return super().default(obj)


def write_json(data, filename):
    filepath = OUTPUT_DIR / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    # allow_nan=False forces valid JSON — we pre-sanitize NaN to None before calling
    with open(filepath, 'w') as f:
        json.dump(data, f, separators=(',', ':'), cls=NumpyEncoder, allow_nan=False)
    size = filepath.stat().st_size
    print(f"  {filename}: {size:,} bytes")


def safe_str(val):
    """Return the string unless it's NaN, in which case return None."""
    if val is None:
        return None
    if isinstance(val, float) and np.isnan(val):
        return None
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    return str(val)


def safe_float(val, default=0.0, precision=None):
    """Return float unless NaN, in which case return default. Optionally round."""
    try:
        if val is None or pd.isna(val):
            return default
        f = float(val)
        return round(f, precision) if precision is not None else f
    except (TypeError, ValueError):
        return default


def all_dates():
    return [str(d.date()) for d in pd.date_range(start=START_DATE, end=END_DATE)]


# ---------------------------------------------------------------------------
# Shared data builders
# ---------------------------------------------------------------------------

def build_dates():
    dates = all_dates()
    write_json({'dates': dates, 'start_date': START_DATE, 'end_date': END_DATE}, 'dates.json')
    return dates


def build_covid_stats(df_stats):
    """Cumulative deaths and cases summed across all countries, keyed by date."""
    result = {}
    for date in all_dates():
        day = df_stats[df_stats['date'] == date]
        deaths = day['cumDeathsByDeathDate'].sum()
        cases = day['cumCasesByPublishDate'].sum()
        result[date] = {
            'deaths': 0 if pd.isna(deaths) else int(deaths),
            'cases': 0 if pd.isna(cases) else int(cases),
        }
    write_json(result, 'covid_stats.json')


def build_r_numbers(r_df):
    """R-number lookup: list of {start, end, r} week-pair objects."""
    weeks = r_df['date'].tolist()
    pairs = []
    for i in range(len(weeks) - 1):
        row = r_df[r_df['date'] == weeks[i]]
        upper = float(row['upper'].iloc[0]) if not row.empty else 0
        lower = float(row['lower'].iloc[0]) if not row.empty else 0
        avg_r = round((upper + lower) / 2, 2)
        pairs.append({
            'start': weeks[i],
            'end': weeks[i + 1],
            'r': f"~{avg_r}" if avg_r != 0 else 'N/A',
        })
    write_json(pairs, 'r_numbers.json')


def build_events(df_events):
    """Events array (one entry per date, empty string if no event) + key events list."""
    dates = all_dates()  # YYYY-MM-DD strings

    # CSV dates are ISO (YYYY-MM-DD). Don't pass dayfirst=True — it silently
    # swaps month/day when the day value is <= 12, producing corrupted dates.
    event_map = {}
    for _, row in df_events.iterrows():
        raw = str(row['Date']).strip()
        try:
            parsed = pd.to_datetime(raw)
            iso = parsed.strftime('%Y-%m-%d')
            # Only keep events within the dashboard's date range
            if START_DATE <= iso <= END_DATE:
                event_map[iso] = row['Event']
        except Exception:
            pass

    events_array = [event_map.get(d, '') for d in dates]
    key_events = [{'date': d, 'event': e} for d, e in sorted(event_map.items())]
    write_json({'events_array': events_array, 'key_events': key_events}, 'events.json')
    return events_array


def build_news(news_df):
    """News headlines grouped by date."""
    result = {}
    for date, group in news_df.groupby('Date'):
        result[date] = [{'headline': r['Headline'], 'url': r['URL']} for _, r in group.iterrows()]
    write_json(result, 'news.json')


def build_covid_stats_ma(df_stats):
    """7-day MA of new deaths and new cases per country."""
    df = df_stats.copy()
    for col in ['newDeathsByDeathDate', 'newCasesByPublishDate']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(float)

    for country in COUNTRIES:
        mask = df['country'] == country
        for col in ['newDeathsByDeathDate', 'newCasesByPublishDate']:
            df.loc[mask, col] = df.loc[mask, col].rolling(window=MA_WINDOW).mean().fillna(0)

    result = []
    for _, row in df.iterrows():
        result.append({
            'date': row['date'],
            'country': row['country'],
            'deaths': round(float(row['newDeathsByDeathDate']), 2),
            'cases': round(float(row['newCasesByPublishDate']), 2),
        })
    write_json(result, 'covid_stats_ma.json')


def copy_geojson():
    src = SOURCE_DIR / 'geojson' / 'uk_counties_simpler.json'
    dst = OUTPUT_DIR / 'geojson.json'
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"  geojson.json: {dst.stat().st_size:,} bytes")


# ---------------------------------------------------------------------------
# Per-topic data builders
# ---------------------------------------------------------------------------

def build_county_sentiment(topic, geo_df):
    """Daily county-level sentiment keyed by date."""
    result = {}
    for date, group in geo_df.groupby('date'):
        counties = []
        for _, row in group.iterrows():
            counties.append({
                'id': int(safe_float(row.get('id', 0), default=0)),
                'county': safe_str(row.get('county')) or '',
                'country': safe_str(row.get('country')) or '',
                'nn': safe_float(row.get('nn-score_avg'), precision=4),
                'vader': safe_float(row.get('vader-score_avg'), precision=4),
                'textblob': safe_float(row.get('textblob-score_avg'), precision=4),
                'native': safe_float(row.get('native-score_avg'), precision=4),
            })
        result[str(date)] = counties
    write_json(result, f'{topic}/county_sentiment.json')


def build_sentiment_counts(topic, all_sent_df):
    """Pre-aggregated prediction counts: {date: {nlp: {country: {neg,neu,pos}}}}."""
    df = all_sent_df.copy()
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')

    result = {}
    for date, day_data in df.groupby('date'):
        nlp_data = {}
        for nlp_type in NLP_TYPES:
            pred_col = PREDICTION_COLS[nlp_type]
            if pred_col not in day_data.columns:
                continue
            country_data = {}
            for country in COUNTRIES:
                cdf = day_data[day_data['country'] == country]
                counts = cdf[pred_col].value_counts()
                country_data[country] = {
                    'neg': int(counts.get('neg', 0)),
                    'neu': int(counts.get('neu', 0)),
                    'pos': int(counts.get('pos', 0)),
                }
            nlp_data[nlp_type] = country_data
        result[date] = nlp_data
    write_json(result, f'{topic}/sentiment_counts.json')


def build_sentiment_ma(topic, geo_df):
    """7-day MA of sentiment aggregated to country level."""
    dates = all_dates()
    geo_df = geo_df.copy()
    geo_df['date'] = geo_df['date'].astype(str)

    # Aggregate county → country averages
    agg = geo_df.groupby(['date', 'country'])[SCORE_AVG_COLS].mean().reset_index()

    # Ensure every date-country pair exists
    idx = pd.MultiIndex.from_product([dates, COUNTRIES], names=['date', 'country'])
    agg = agg.set_index(['date', 'country']).reindex(idx, fill_value=0.0).reset_index()

    # Apply 7-day MA per country
    for country in COUNTRIES:
        mask = agg['country'] == country
        for col in SCORE_AVG_COLS:
            agg.loc[mask, col] = agg.loc[mask, col].astype(float).rolling(window=MA_WINDOW).mean().fillna(0)

    result = []
    for _, row in agg.iterrows():
        result.append({
            'date': row['date'],
            'country': row['country'],
            'nn': round(float(row['nn-score_avg']), 6),
            'vader': round(float(row['vader-score_avg']), 6),
            'textblob': round(float(row['textblob-score_avg']), 6),
            'native': round(float(row['native-score_avg']), 6),
        })
    write_json(result, f'{topic}/sentiment_ma.json')


def build_sentiment_comp(topic, all_sent_df):
    """7-day MA comparison of NLP techniques (daily average across all tweets)."""
    df = all_sent_df.copy()
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    dates = all_dates()

    # Average each score column per date
    agg_cols = {v: 'mean' for v in SCORE_COLS.values()}
    daily = df.groupby('date').agg(agg_cols).reindex(dates, fill_value=0.0).reset_index()
    daily.columns = ['date'] + list(SCORE_COLS.keys())

    # Apply 7-day MA
    for col in NLP_TYPES:
        daily[col] = daily[col].astype(float).rolling(window=MA_WINDOW).mean().fillna(0)

    result = [
        {
            'date': row['date'],
            'nn': round(float(row['nn']), 6),
            'vader': round(float(row['vader']), 6),
            'textblob': round(float(row['textblob']), 6),
            'native': round(float(row['native']), 6),
        }
        for _, row in daily.iterrows()
    ]
    write_json(result, f'{topic}/sentiment_comp.json')


def build_tweet_volume_ma(topic, tweet_count_df):
    """7-day MA of tweet volume per country."""
    df = tweet_count_df.copy()
    for country in COUNTRIES:
        if country in df.columns:
            df[country] = df[country].astype(float).rolling(window=MA_WINDOW).mean().fillna(0)

    result = []
    for _, row in df.iterrows():
        record = {'date': row['date']}
        for country in COUNTRIES:
            record[country] = round(float(row.get(country, 0)), 2)
        result.append(record)
    write_json(result, f'{topic}/tweet_volume_ma.json')


def build_hashtags(topic, hashtags_df):
    """Parsed hashtags keyed by date."""
    result = {}
    for _, row in hashtags_df.iterrows():
        date = str(row['date'])
        raw = str(row['top_ten_hashtags'])
        hashtags = []
        for match in re.findall(r"\((.*?)\)", raw):
            parts = match.split(',')
            if len(parts) >= 2:
                tag = parts[0].strip().replace("'", '').replace('"', '')
                try:
                    count = int(parts[1].strip())
                except ValueError:
                    continue
                hashtags.append({'tag': '#' + tag, 'count': count})
        result[date] = hashtags
    write_json(result, f'{topic}/hashtags.json')


def build_emojis(topic, emojis_df):
    """Weekly emoji data grouped by date."""
    result = {}
    for date, group in emojis_df.groupby('date'):
        group = group.sort_values('count', ascending=False)
        result[str(date)] = [
            {
                'emoji': safe_str(r.get('emoji')) or '',
                'count': int(safe_float(r.get('count'), default=0)),
                'colour': safe_str(r.get('colour')) or '#9c9890',
            }
            for _, r in group.iterrows()
        ]
    write_json(result, f'{topic}/emojis.json')


def build_notable_days(topic, notable_df):
    """Notable days grouped by sentiment type."""
    result = {}
    for sent_type in NLP_TYPES:
        rows = notable_df[notable_df['sentiment_type'] == sent_type]
        result[sent_type] = [
            {
                'label': safe_str(r.get('notable_label')) or '',
                'date': safe_str(r.get('date')) or '',
                'rate': safe_float(r.get('rate'), precision=4),
            }
            for _, r in rows.iterrows()
        ]
    write_json(result, f'{topic}/notable_days.json')


def build_scatter(topic, scatter_df):
    """Scatter/correlation data."""
    result = []
    for _, row in scatter_df.iterrows():
        result.append({
            'country': safe_str(row.get('country')) or '',
            'volume': safe_float(row.get('volume'), precision=4),
            'deaths': safe_float(row.get('deaths'), precision=4),
            'cases': safe_float(row.get('cases'), precision=4),
            'nn': safe_float(row.get('nn-score_avg'), precision=4),
            'textblob': safe_float(row.get('textblob-score_avg'), precision=4),
            'vader': safe_float(row.get('vader-score_avg'), precision=4),
            'native': safe_float(row.get('native-score_avg'), precision=4),
        })
    write_json(result, f'{topic}/scatter.json')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=== Building static data files ===")
    print(f"Source: {SOURCE_DIR}")
    print(f"Output: {OUTPUT_DIR}\n")

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    # Load shared data
    print("Loading shared data...")
    df_covid_stats = pd.read_csv(SOURCE_DIR / 'covid-data/uk_covid_stats.csv', skipinitialspace=True)
    r_numbers_df = pd.read_csv(SOURCE_DIR / 'covid-data/r_numbers.csv')
    # key_events.csv has unescaped commas in event text - parse manually on last comma
    event_rows = []
    with open(SOURCE_DIR / 'events/key_events.csv', 'r') as f:
        next(f)  # skip header
        for line in f:
            line = line.rstrip()
            if not line:
                continue
            idx = line.rfind(',')
            if idx > 0:
                event_rows.append({'Event': line[:idx].strip(), 'Date': line[idx + 1:].strip()})
    df_events = pd.DataFrame(event_rows)
    news_df = pd.read_csv(SOURCE_DIR / 'events/news_timeline.csv')

    # Load per-topic data
    topic_data = {}
    for topic in TOPICS:
        print(f"Loading {topic} data...")
        topic_data[topic] = {
            'geo': pd.read_csv(SOURCE_DIR / f'{topic}/daily_sentiment_county_updated_locations.csv'),
            'all_sent': pd.read_csv(SOURCE_DIR / f'{topic}/all_tweet_sentiments.csv'),
            'hashtags': pd.read_csv(SOURCE_DIR / f'{topic}/top_ten_hashtags_per_day.csv'),
            'emojis': pd.read_csv(SOURCE_DIR / f'{topic}/weekly_emojis_with_colours.csv'),
            'tweet_count': pd.read_csv(SOURCE_DIR / f'{topic}/daily_tweet_count_country.csv'),
            'notable': pd.read_csv(SOURCE_DIR / f'{topic}/notable_days_months.csv'),
            'scatter': pd.read_csv(SOURCE_DIR / f'{topic}/scatter.csv'),
        }

    # Build shared files
    print("\n[Shared data]")
    build_dates()
    build_covid_stats(df_covid_stats)
    build_r_numbers(r_numbers_df)
    build_events(df_events)
    build_news(news_df)
    build_covid_stats_ma(df_covid_stats)
    copy_geojson()

    # Build per-topic files
    for topic in TOPICS:
        print(f"\n[{topic}]")
        td = topic_data[topic]
        build_county_sentiment(topic, td['geo'])
        print(f"  Processing {topic} sentiment counts (this may take a moment)...")
        build_sentiment_counts(topic, td['all_sent'])
        build_sentiment_ma(topic, td['geo'])
        print(f"  Processing {topic} sentiment comparison...")
        build_sentiment_comp(topic, td['all_sent'])
        build_tweet_volume_ma(topic, td['tweet_count'])
        build_hashtags(topic, td['hashtags'])
        build_emojis(topic, td['emojis'])
        build_notable_days(topic, td['notable'])
        build_scatter(topic, td['scatter'])

    total = sum(f.stat().st_size for f in OUTPUT_DIR.rglob('*.json'))
    print(f"\n=== Build complete! Total: {total:,} bytes ({total / 1024 / 1024:.1f} MB) ===")


if __name__ == '__main__':
    main()
