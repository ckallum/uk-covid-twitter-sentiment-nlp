"""
Shared data and utilities for Vercel serverless functions
"""
import json
import os
import pandas as pd
from pathlib import Path
import sys

# Add the project root to the Python path for Vercel
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from utils.formatting import create_event_array
from utils.formatting import (
    format_df_ma_stats, format_df_ma_sent, format_df_ma_tweet_vol, 
    format_df_corr, format_df_notable_days, format_df_ma_sent_comp
)
from utils.plotting import (
    plot_dropdown_sent_vs_vol, plot_covid_stats, plot_hashtag_table, 
    plot_sentiment, plot_corr_mat, plot_sentiment_bar, plot_emoji_bar_chart, 
    emoji_to_colour, plot_notable_days, plot_sentiment_comp
)

# Global data variables
_data_loaded = False
_data = {}

def load_data():
    """Load all data files once and cache them"""
    global _data_loaded, _data
    
    if _data_loaded:
        return _data
    
    try:
        # Core data files
        geojson_path = BASE_DIR / 'data/geojson/uk_counties_simpler.json'
        with open(geojson_path, 'r') as f:
            _data['uk_counties'] = json.load(f)
            
        _data['df_covid_stats'] = pd.read_csv(
            BASE_DIR / 'data/covid-data/uk_covid_stats.csv', skipinitialspace=True)
        _data['r_numbers'] = pd.read_csv(BASE_DIR / 'data/covid-data/r_numbers.csv')
        _data['df_events'] = pd.read_csv(BASE_DIR / 'data/events/key_events.csv',
                              skipinitialspace=True, usecols=['Date', 'Event'])
        _data['counties'] = pd.read_csv(
            BASE_DIR / 'data/geojson/uk-district-list-all.csv')['county'].tolist()
        
        # Tweet data files
        _data['hashtags_covid'] = pd.read_csv(BASE_DIR / 'data/covid/top_ten_hashtags_per_day.csv')
        _data['hashtags_lockdown'] = pd.read_csv(BASE_DIR / 'data/lockdown/top_ten_hashtags_per_day.csv')
        _data['geo_df_covid'] = pd.read_csv(
            BASE_DIR / 'data/covid/daily_sentiment_county_updated_locations.csv')
        _data['geo_df_lockdown'] = pd.read_csv(
            BASE_DIR / 'data/lockdown/daily_sentiment_county_updated_locations.csv')
        _data['tweet_count_covid'] = pd.read_csv(BASE_DIR / 'data/covid/daily_tweet_count_country.csv')
        _data['tweet_count_lockdown'] = pd.read_csv(
            BASE_DIR / 'data/lockdown/daily_tweet_count_country.csv')
        _data['all_sentiments_covid'] = pd.read_csv(BASE_DIR / 'data/covid/all_tweet_sentiments.csv')
        _data['all_sentiments_lockdown'] = pd.read_csv(BASE_DIR / 'data/lockdown/all_tweet_sentiments.csv')
        _data['notable_days_covid'] = pd.read_csv(BASE_DIR / 'data/covid/notable_days_months.csv')
        _data['notable_days_lockdown'] = pd.read_csv(BASE_DIR / 'data/lockdown/notable_days_months.csv')
        _data['scatter_covid'] = pd.read_csv(BASE_DIR / 'data/covid/scatter.csv')
        _data['scatter_lockdown'] = pd.read_csv(BASE_DIR / 'data/lockdown/scatter.csv')
        _data['emojis_covid'] = pd.read_csv(BASE_DIR / 'data/covid/weekly_emojis_with_colours.csv')
        _data['emojis_lockdown'] = pd.read_csv(BASE_DIR / 'data/lockdown/weekly_emojis_with_colours.csv')
        _data['news_df'] = pd.read_csv(BASE_DIR / 'data/events/news_timeline.csv')
        
        _data_loaded = True
        
    except Exception as e:
        print(f"Error loading data files: {e}")
        # Create empty fallbacks
        _data = {key: pd.DataFrame() if 'df' in key or 'covid' in key or 'lockdown' in key 
                 else [] if key == 'counties' else {} for key in _data.keys()}
    
    return _data

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
    """Get organized data sources"""
    data = load_data()
    
    return {
        'hashtag_data_sources': {
            'covid': data['hashtags_covid'],
            'lockdown': data['hashtags_lockdown']
        },
        'geo_df_data_sources': {
            'covid': data['geo_df_covid'],
            'lockdown': data['geo_df_lockdown']
        },
        'complete_data_sources': {
            'covid': data['all_sentiments_covid'],
            'lockdown': data['all_sentiments_lockdown']
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