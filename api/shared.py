"""
Shared data and utilities for Vercel serverless functions
"""
import json
import os
import pandas as pd
from pathlib import Path
import sys
import requests
from io import StringIO

# Add the project root to the Python path for Vercel
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))


from utils.plotting import (
    plot_dropdown_sent_vs_vol, plot_covid_stats, plot_hashtag_table, 
    plot_sentiment, plot_corr_mat, plot_sentiment_bar, plot_emoji_bar_chart, 
    emoji_to_colour, plot_notable_days, plot_sentiment_comp
)

# Data URLs - replace with your actual Vercel Blob URLs
DATA_URLS = {
    # Core data
    'uk_counties_geojson': 'https://raw.githubusercontent.com/ckallum/uk-covid-twitter-sentiment-nlp/main/data/geojson/uk_counties_simpler.json',
    'uk_covid_stats': 'https://raw.githubusercontent.com/ckallum/uk-covid-twitter-sentiment-nlp/main/data/covid-data/uk_covid_stats.csv',
    'r_numbers': 'https://raw.githubusercontent.com/ckallum/uk-covid-twitter-sentiment-nlp/main/data/covid-data/r_numbers.csv',
    'key_events': 'https://raw.githubusercontent.com/ckallum/uk-covid-twitter-sentiment-nlp/main/data/events/key_events.csv',
    'uk_counties_list': 'https://raw.githubusercontent.com/ckallum/uk-covid-twitter-sentiment-nlp/main/data/geojson/uk-district-list-all.csv',
    
    # COVID data - using smaller files first
    'hashtags_covid': 'https://raw.githubusercontent.com/ckallum/uk-covid-twitter-sentiment-nlp/main/data/covid/top_ten_hashtags_per_day.csv',
    'hashtags_lockdown': 'https://raw.githubusercontent.com/ckallum/uk-covid-twitter-sentiment-nlp/main/data/lockdown/top_ten_hashtags_per_day.csv',
    'notable_days_covid': 'https://raw.githubusercontent.com/ckallum/uk-covid-twitter-sentiment-nlp/main/data/covid/notable_days_months.csv',
    'notable_days_lockdown': 'https://raw.githubusercontent.com/ckallum/uk-covid-twitter-sentiment-nlp/main/data/lockdown/notable_days_months.csv',
    'tweet_count_covid': 'https://raw.githubusercontent.com/ckallum/uk-covid-twitter-sentiment-nlp/main/data/covid/daily_tweet_count_country.csv',
    'tweet_count_lockdown': 'https://raw.githubusercontent.com/ckallum/uk-covid-twitter-sentiment-nlp/main/data/lockdown/daily_tweet_count_country.csv',
    'weekly_emojis_covid': 'https://raw.githubusercontent.com/ckallum/uk-covid-twitter-sentiment-nlp/main/data/covid/weekly_emojis_with_colours.csv',
    'weekly_emojis_lockdown': 'https://raw.githubusercontent.com/ckallum/uk-covid-twitter-sentiment-nlp/main/data/lockdown/weekly_emojis_with_colours.csv',
    'scatter_covid': 'https://raw.githubusercontent.com/ckallum/uk-covid-twitter-sentiment-nlp/main/data/covid/scatter.csv',
    'scatter_lockdown': 'https://raw.githubusercontent.com/ckallum/uk-covid-twitter-sentiment-nlp/main/data/lockdown/scatter.csv',
    
    # Large files - load on demand only
    'geo_df_covid': 'https://raw.githubusercontent.com/ckallum/uk-covid-twitter-sentiment-nlp/main/data/covid/daily_sentiment_county_updated_locations.csv',
    'geo_df_lockdown': 'https://raw.githubusercontent.com/ckallum/uk-covid-twitter-sentiment-nlp/main/data/lockdown/daily_sentiment_county_updated_locations.csv',
}

# Global data variables
_data_loaded = False
_data = {}

def load_from_url_or_local(url, local_path, file_type='csv'):
    """Load data from URL with fallback to local file"""
    try:
        print(f"Loading from URL: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        if file_type == 'json':
            return response.json()
        elif file_type == 'csv':
            return pd.read_csv(StringIO(response.text))
    except Exception as e:
        print(f"Failed to load from URL {url}: {e}")
        # Fallback to local file for development
        try:
            local_file_path = BASE_DIR / local_path
            if local_file_path.exists():
                print(f"Falling back to local file: {local_file_path}")
                if file_type == 'json':
                    with open(local_file_path, 'r') as f:
                        return json.load(f)
                elif file_type == 'csv':
                    return pd.read_csv(local_file_path)
        except Exception as local_e:
            print(f"Failed to load local file {local_path}: {local_e}")
        
        # Return empty data as last resort
        if file_type == 'json':
            return {}
        elif file_type == 'csv':
            return pd.DataFrame()

def load_data():
    """Load essential data files once and cache them"""
    global _data_loaded, _data
    
    if _data_loaded:
        return _data
    
    try:
        # Load essential data only
        print("Loading essential data...")
        
        # Core small files
        _data['uk_counties'] = load_from_url_or_local(
            DATA_URLS['uk_counties_geojson'], 
            'data/geojson/uk_counties_simpler.json', 
            'json'
        )
        
        _data['df_covid_stats'] = load_from_url_or_local(
            DATA_URLS['uk_covid_stats'],
            'data/covid-data/uk_covid_stats.csv'
        )
        
        _data['r_numbers'] = load_from_url_or_local(
            DATA_URLS['r_numbers'],
            'data/covid-data/r_numbers.csv'
        )
        
        _data['df_events'] = load_from_url_or_local(
            DATA_URLS['key_events'],
            'data/events/key_events.csv'
        )[['Date', 'Event']] if not load_from_url_or_local(DATA_URLS['key_events'], 'data/events/key_events.csv').empty else pd.DataFrame()
        
        counties_df = load_from_url_or_local(
            DATA_URLS['uk_counties_list'],
            'data/geojson/uk-district-list-all.csv'
        )
        _data['counties'] = counties_df['county'].tolist() if 'county' in counties_df.columns else []
        
        # Load smaller datasets
        _data['hashtags_covid'] = load_from_url_or_local(
            DATA_URLS['hashtags_covid'],
            'data/covid/top_ten_hashtags_per_day.csv'
        )
        
        _data['hashtags_lockdown'] = load_from_url_or_local(
            DATA_URLS['hashtags_lockdown'],
            'data/lockdown/top_ten_hashtags_per_day.csv'
        )
        
        _data['notable_days_covid'] = load_from_url_or_local(
            DATA_URLS['notable_days_covid'],
            'data/covid/notable_days_months.csv'
        )
        
        _data['notable_days_lockdown'] = load_from_url_or_local(
            DATA_URLS['notable_days_lockdown'],
            'data/lockdown/notable_days_months.csv'
        )
        
        _data['tweet_count_covid'] = load_from_url_or_local(
            DATA_URLS['tweet_count_covid'],
            'data/covid/daily_tweet_count_country.csv'
        )
        
        _data['tweet_count_lockdown'] = load_from_url_or_local(
            DATA_URLS['tweet_count_lockdown'],
            'data/lockdown/daily_tweet_count_country.csv'
        )
        
        _data['emojis_covid'] = load_from_url_or_local(
            DATA_URLS['weekly_emojis_covid'],
            'data/covid/weekly_emojis_with_colours.csv'
        )
        
        _data['emojis_lockdown'] = load_from_url_or_local(
            DATA_URLS['weekly_emojis_lockdown'],
            'data/lockdown/weekly_emojis_with_colours.csv'
        )
        
        _data['scatter_covid'] = load_from_url_or_local(
            DATA_URLS['scatter_covid'],
            'data/covid/scatter.csv'
        )
        
        _data['scatter_lockdown'] = load_from_url_or_local(
            DATA_URLS['scatter_lockdown'],
            'data/lockdown/scatter.csv'
        )
        
        print("Essential data loaded successfully")
        _data_loaded = True
        
    except Exception as e:
        print(f"Error loading data files: {e}")
        # Create empty fallbacks
        _data = {
            'uk_counties': {},
            'counties': [],
            'df_covid_stats': pd.DataFrame(),
            'r_numbers': pd.DataFrame(),
            'df_events': pd.DataFrame(),
            'hashtags_covid': pd.DataFrame(),
            'hashtags_lockdown': pd.DataFrame(),
            'notable_days_covid': pd.DataFrame(),
            'notable_days_lockdown': pd.DataFrame(),
            'tweet_count_covid': pd.DataFrame(),
            'tweet_count_lockdown': pd.DataFrame(),
            'emojis_covid': pd.DataFrame(),
            'emojis_lockdown': pd.DataFrame(),
            'scatter_covid': pd.DataFrame(),
            'scatter_lockdown': pd.DataFrame(),
        }
    
    return _data

def load_large_data_on_demand(data_type, topic):
    """Load large datasets only when needed"""
    cache_key = f"{data_type}_{topic}"
    
    if cache_key in _data:
        return _data[cache_key]
    
    try:
        if data_type == 'geo_df':
            url = DATA_URLS[f'geo_df_{topic}']
            local_path = f'data/{topic}/daily_sentiment_county_updated_locations.csv'
        elif data_type == 'all_sentiments':
            # These are the largest files - only load if absolutely necessary
            print(f"Warning: Loading large sentiment data for {topic}")
            return pd.DataFrame()  # Return empty for now to avoid size issues
        else:
            return pd.DataFrame()
        
        data = load_from_url_or_local(url, local_path)
        _data[cache_key] = data
        return data
        
    except Exception as e:
        print(f"Error loading large data {cache_key}: {e}")
        return pd.DataFrame()

# Constants and mappings
COUNTRIES = ['England', 'Scotland', 'Northern Ireland', 'Wales']

EMOJI_WORDCLOUD_URLS = {'covid': 'assets/covid_emoji_wordcloud.png',
                       'lockdown': 'assets/lockdown_emoji_wordcloud.png'}
WORDCLOUD_URLS = {'covid': 'assets/covid_wordcloud.png',
                 'lockdown': 'assets/lockdown_wordcloud.png'}

SENTIMENT_DROPDOWN_VALUE_TO_AVG_SCORE = {
    'nn': 'nn-score_avg', 'textblob': 'textblob-score_avg',
    'vader': 'vader-score_avg', 'native': 'native-score_avg'
}
SENTIMENT_DROPDOWN_VALUE_TO_SCORE = {
    'nn': 'nn-score', 'textblob': 'textblob-score',
    'vader': 'vader-score', 'native': 'native-score'
}
SENTIMENT_DROPDOWN_VALUE_TO_PREDICTIONS = {
    'nn': 'nn-predictions', 'textblob': 'textblob-predictions',
    'vader': 'vader-predictions', 'native': 'native-predictions'
}

def get_data_sources():
    """Get organized data sources with on-demand loading for large files"""
    data = load_data()
    
    return {
        'hashtag_data_sources': {
            'covid': data['hashtags_covid'],
            'lockdown': data['hashtags_lockdown']
        },
        'geo_df_data_sources': {
            'covid': load_large_data_on_demand('geo_df', 'covid'),
            'lockdown': load_large_data_on_demand('geo_df', 'lockdown')
        },
        'complete_data_sources': {
            'covid': load_large_data_on_demand('all_sentiments', 'covid'),
            'lockdown': load_large_data_on_demand('all_sentiments', 'lockdown')
        },
        'tweet_counts_sources': {
            'covid': data['tweet_count_covid'],
            'lockdown': data['tweet_count_lockdown']
        },
        'notable_days_sources': {
            'covid': data['notable_days_covid'],
            'lockdown': data['notable_days_lockdown']
        },
        'scatter_sources': {
            'covid': data['scatter_covid'],
            'lockdown': data['scatter_lockdown']
        }
    } 