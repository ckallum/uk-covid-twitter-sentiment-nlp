"""
Robust API with case-sensitive file handling for Heroku deployment
"""
import os
import json
import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from flask import Flask, jsonify, request, send_from_directory
from pathlib import Path

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

# Create the Flask app
app = Flask(__name__, static_folder="static")

# Define the base directory
BASE_DIR = Path(__file__).resolve().parent

# Case sensitivity helper functions
def find_case_insensitive_path(base_path, path_components):
    """
    Recursively find a path regardless of case sensitivity
    
    Args:
        base_path: The starting directory (Path object)
        path_components: List of directory/file names to navigate
        
    Returns:
        Path object if found, None if not found
    """
    if not path_components:
        return base_path
        
    if not base_path.exists() or not base_path.is_dir():
        return None
        
    target = path_components[0]
    remaining = path_components[1:]
    
    # Try exact match first
    next_path = base_path / target
    if next_path.exists():
        return find_case_insensitive_path(next_path, remaining)
    
    # Try case-insensitive match
    for item in base_path.iterdir():
        if item.name.lower() == target.lower():
            return find_case_insensitive_path(item, remaining)
    
    # Not found
    return None

def get_file_path(relative_path):
    """
    Find a file path regardless of case sensitivity
    
    Args:
        relative_path: String path relative to BASE_DIR
        
    Returns:
        Path object if found, None if not found
    """
    components = relative_path.split('/')
    return find_case_insensitive_path(BASE_DIR, components)

def read_csv_case_insensitive(relative_path, **kwargs):
    """Read a CSV file with case-insensitive path handling"""
    path = get_file_path(relative_path)
    if path and path.exists():
        return pd.read_csv(path, **kwargs)
    else:
        print(f"Warning: Could not find file {relative_path}")
        return pd.DataFrame()

def read_json_case_insensitive(relative_path):
    """Read a JSON file with case-insensitive path handling"""
    path = get_file_path(relative_path)
    if path and path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    else:
        print(f"Warning: Could not find file {relative_path}")
        return {}

# READ DATA - with case insensitive path handling
try:
    print("Loading data files...")
    
    # Load core data files
    df_covid_stats = read_csv_case_insensitive('data/covid-data/uk_covid_stats.csv', skipinitialspace=True)
    uk_counties = read_json_case_insensitive('data/geojson/uk_counties_simpler.json')
    r_numbers = read_csv_case_insensitive('data/covid-data/r_numbers.csv')
    df_events = read_csv_case_insensitive('data/events/key_events.csv', skipinitialspace=True, usecols=['Date', 'Event'])
    
    # Get county list
    counties_file = get_file_path('data/geojson/uk-district-list-all.csv')
    if counties_file and counties_file.exists():
        counties = pd.read_csv(counties_file)['county'].tolist()
    else:
        print("Warning: Could not find counties file")
        counties = []
    
    # Load hashtags and geo data
    hashtags_covid = read_csv_case_insensitive('data/covid/top_ten_hashtags_per_day.csv')
    hashtags_lockdown = read_csv_case_insensitive('data/lockdown/top_ten_hashtags_per_day.csv')
    geo_df_covid = read_csv_case_insensitive('data/covid/daily_sentiment_county_updated_locations.csv')
    geo_df_lockdown = read_csv_case_insensitive('data/lockdown/daily_sentiment_county_updated_locations.csv')
    
    # Load tweet counts
    tweet_count_covid = read_csv_case_insensitive('data/covid/daily_tweet_count_country.csv')
    tweet_count_lockdown = read_csv_case_insensitive('data/lockdown/daily_tweet_count_country.csv')
    
    # Load sentiment data
    all_sentiments_covid = read_csv_case_insensitive('data/covid/all_tweet_sentiments.csv')
    all_sentiments_lockdown = read_csv_case_insensitive('data/lockdown/all_tweet_sentiments.csv')
    
    # Load notable days and scatter data
    notable_days_covid = read_csv_case_insensitive('data/covid/notable_days_months.csv')
    notable_days_lockdown = read_csv_case_insensitive('data/lockdown/notable_days_months.csv')
    scatter_covid = read_csv_case_insensitive('data/covid/scatter.csv')
    scatter_lockdown = read_csv_case_insensitive('data/lockdown/scatter.csv')
    
    # Load emoji data
    emojis_covid = read_csv_case_insensitive('data/covid/weekly_emojis_with_colours.csv')
    emojis_lockdown = read_csv_case_insensitive('data/lockdown/weekly_emojis_with_colours.csv')
    news_df = read_csv_case_insensitive('data/events/news_timeline.csv')
    
    print("Data files loaded successfully")
except Exception as e:
    print(f"Error loading data files: {e}")
    # Create empty fallback data
    uk_counties = {}
    counties = []
    df_covid_stats = r_numbers = df_events = pd.DataFrame()
    hashtags_covid = hashtags_lockdown = geo_df_covid = geo_df_lockdown = pd.DataFrame()
    tweet_count_covid = tweet_count_lockdown = all_sentiments_covid = all_sentiments_lockdown = pd.DataFrame()
    notable_days_covid = notable_days_lockdown = scatter_covid = scatter_lockdown = pd.DataFrame()
    emojis_covid = emojis_lockdown = news_df = pd.DataFrame()

# Constants
countries = ['England', 'Scotland', 'Northern Ireland', 'Wales']

# Data Sources
emoji_wordcloud_urls = {'covid': 'covid_emoji_wordcloud.png',
                  'lockdown': 'lockdown_emoji_wordcloud.png'}
wordcloud_urls = {'covid': 'covid_wordcloud.png',
                  'lockdown': 'lockdown_wordcloud.png'}
hashtag_data_sources = {'covid': hashtags_covid,
                        'lockdown': hashtags_lockdown}
geo_df_data_sources = {'covid': geo_df_covid,
                       'lockdown': geo_df_lockdown}

complete_data_sources = {'covid': all_sentiments_covid,
                         'lockdown': all_sentiments_lockdown}

sentiment_dropdown_value_to_avg_score = {'nn': 'nn-score_avg', 'textblob': 'textblob-score_avg',
                                         'vader': 'vader-score_avg', 'native': 'native-score_avg'}
sentiment_dropdown_value_to_score = {'nn': 'nn-score', 'textblob': 'textblob-score',
                                     'vader': 'vader-score', 'native': 'native-score'}
sentiment_dropdown_value_to_predictions = {'nn': 'nn-predictions', 'textblob': 'textblob-predictions',
                                           'vader': 'vader-predictions', 'native': 'native-predictions'}
tweet_counts_sources = {'covid': tweet_count_covid,
                        'lockdown': tweet_count_lockdown}
regions_lists = {'county': counties, 'country': countries}

notable_days_sources = {'covid': notable_days_covid,
                        'lockdown': notable_days_lockdown}

scatter_sources = {'covid': scatter_covid, 'lockdown': scatter_lockdown}

# Process data if available
try:
    # Formatted tweet data
    formatted_tweet_count = {
        'covid': format_df_ma_tweet_vol(tweet_count_covid, countries) if not tweet_count_covid.empty else pd.DataFrame(),
        'lockdown': format_df_ma_tweet_vol(tweet_count_lockdown, countries) if not tweet_count_lockdown.empty else pd.DataFrame()
    }
    
    # Formatted sentiment data
    formatted_tweet_sent = {
        'covid': format_df_ma_sent(geo_df_covid) if not geo_df_covid.empty else pd.DataFrame(),
        'lockdown': format_df_ma_sent(geo_df_lockdown) if not geo_df_lockdown.empty else pd.DataFrame()
    }
    
    # Formatted COVID stats
    formatted_covid_stats = format_df_ma_stats(df_covid_stats, countries) if not df_covid_stats.empty else pd.DataFrame()
    
    # Formatted sentiment comparison
    formatted_sent_comp = {
        'covid': format_df_ma_sent_comp(all_sentiments_covid) if not all_sentiments_covid.empty else pd.DataFrame(),
        'lockdown': format_df_ma_sent_comp(all_sentiments_lockdown) if not all_sentiments_lockdown.empty else pd.DataFrame()
    }
except Exception as e:
    print(f"Error formatting data: {e}")
    # Create empty defaults
    formatted_tweet_count = {'covid': pd.DataFrame(), 'lockdown': pd.DataFrame()}
    formatted_tweet_sent = {'covid': pd.DataFrame(), 'lockdown': pd.DataFrame()}
    formatted_covid_stats = pd.DataFrame()
    formatted_sent_comp = {'covid': pd.DataFrame(), 'lockdown': pd.DataFrame()}

emojis_weekly_source = {'covid': emojis_covid, 'lockdown': emojis_lockdown}

# Dates
if not r_numbers.empty and 'date' in r_numbers.columns:
    weeks = r_numbers['date'].tolist()
    week_pairs = [(weeks[i], weeks[i + 1]) for i in range(0, len(weeks) - 1)]
else:
    weeks = []
    week_pairs = []

start_global = '2020-03-20'
end_global = '2021-03-25'
dates_list = pd.date_range(start=start_global, end=end_global)
str_dates_list = [str(date.date()) for date in dates_list]

# Events
if not df_events.empty:
    events_array = create_event_array(df_events, start_global, end_global)
else:
    events_array = []

# Helper function for converting plotly figures to JSON
def fig_to_json(fig):
    """Convert a plotly figure to a JSON representation for the API"""
    fig_dict = fig.to_dict()
    
    # Convert numpy arrays and data types to Python native types
    import json
    import numpy as np
    
    class NumpyEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, np.integer):
                return int(obj)
            if isinstance(obj, np.floating):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            return super(NumpyEncoder, self).default(obj)
    
    # First convert to JSON string then back to dict to ensure Python native types
    sanitized_dict = json.loads(json.dumps(fig_dict, cls=NumpyEncoder))
    
    return {
        'data': sanitized_dict['data'],
        'layout': sanitized_dict['layout']
    }

def check_between_dates(start, end, current):
    """Check if a date is between two other dates"""
    start, end, current = pd.to_datetime(start, format='%d/%m/%Y'), \
                          pd.to_datetime(end, format='%d/%m/%Y'), \
                          pd.to_datetime(current, format='%Y-%m-%d')
    return start < current <= end

# Health check and debugging endpoints
@app.route('/health')
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "ok"})

@app.route('/debug')
def debug():
    """Debug endpoint to check data loading"""
    data_info = {
        'df_covid_stats': len(df_covid_stats) if hasattr(df_covid_stats, '__len__') else 0,
        'uk_counties': len(uk_counties) if hasattr(uk_counties, '__len__') else 0,
        'counties': len(counties) if hasattr(counties, '__len__') else 0,
        'r_numbers': len(r_numbers) if hasattr(r_numbers, '__len__') else 0,
        'df_events': len(df_events) if hasattr(df_events, '__len__') else 0,
        'hashtags_covid': len(hashtags_covid) if hasattr(hashtags_covid, '__len__') else 0,
        'geo_df_covid': len(geo_df_covid) if hasattr(geo_df_covid, '__len__') else 0,
        'tweet_count_covid': len(tweet_count_covid) if hasattr(tweet_count_covid, '__len__') else 0,
        'all_sentiments_covid': len(all_sentiments_covid) if hasattr(all_sentiments_covid, '__len__') else 0
    }
    
    return jsonify({
        "status": "ok",
        "data_loaded": data_info
    })

@app.route('/favicon.ico')
def favicon():
    """Serve favicon directly"""
    for path in [BASE_DIR / 'static/assets', BASE_DIR / 'assets']:
        if (path / 'favicon.ico').exists():
            return send_from_directory(path, 'favicon.ico')
    
    # Fallback
    return "", 204

# Static file routes
@app.route('/')
def index():
    """Serve the main index.html file"""
    # Find the index.html file regardless of case
    static_path = get_file_path('static')
    if static_path and static_path.exists():
        for item in static_path.iterdir():
            if item.name.lower() == 'index.html':
                return send_from_directory(static_path, item.name)
    
    # Fallback to a simple page
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>COVID Sentiment Analysis</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            h1 { color: #2c3e50; }
            .container { max-width: 800px; margin: 0 auto; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>COVID Sentiment Analysis</h1>
            <p>The API is running but the static files could not be found.</p>
        </div>
    </body>
    </html>
    """

@app.route('/<path:path>')
def static_files(path):
    """Serve static files"""
    # Try to find the file in static directory
    components = ['static'] + path.split('/')
    file_path = find_case_insensitive_path(BASE_DIR, components)
    
    if file_path and file_path.exists() and file_path.is_file():
        # Calculate the parent directory and filename
        parent = file_path.parent
        filename = file_path.name
        return send_from_directory(parent, filename)
    
    return "File not found", 404

# API Routes
@app.route('/api/dates')
def get_dates():
    """Return all dates in the dataset"""
    return jsonify({
        'dates': str_dates_list,
        'start_date': start_global,
        'end_date': end_global
    })

@app.route('/api/covid_stats')
def get_covid_stats():
    """Get COVID stats for a given date"""
    date = request.args.get('date')
    
    if df_covid_stats.empty:
        return jsonify({
            'date': date,
            'total_deaths': 0,
            'total_cases': 0,
            'error': 'No COVID stats data available'
        })
    
    total_deaths = df_covid_stats.loc[df_covid_stats['date'] == date, 'cumDeathsByDeathDate'].sum()
    total_cases = df_covid_stats.loc[df_covid_stats['date'] == date, 'cumCasesByPublishDate'].sum()
    
    return jsonify({
        'date': date,
        'total_deaths': int(total_deaths),
        'total_cases': int(total_cases)
    })

@app.route('/api/r_numbers')
def get_r_numbers():
    """Get R numbers for a given date"""
    date = request.args.get('date')
    r_number = 'N/A'
    
    if not r_numbers.empty:
        for i, (start, end) in enumerate(week_pairs):
            if check_between_dates(start, end, date):
                df = r_numbers.loc[r_numbers['date'] == start]
                # Fix the deprecated Series float conversion
                upper = df['upper'].iloc[0] if not df['upper'].empty else 0
                lower = df['lower'].iloc[0] if not df['lower'].empty else 0
                avg_r = round((upper + lower) / 2, 2)
                if avg_r != 0:
                    r_number = f"~{avg_r}"
    
    return jsonify({
        'date': date,
        'r_number': r_number
    })

@app.route('/api/county_choropleth')
def get_county_choropleth():
    """Get county choropleth map data"""
    date = request.args.get('date')
    nlp_type = request.args.get('nlp_type', 'nn')
    topic = request.args.get('topic', 'covid')
    
    if geo_df_data_sources[topic].empty or not uk_counties:
        return jsonify({
            'error': 'No geo data or UK counties data available'
        })
    
    geo_df = geo_df_data_sources[topic]
    color = sentiment_dropdown_value_to_avg_score[nlp_type]
    
    geo_df = geo_df.loc[geo_df['date'] == date]
    fig = px.choropleth_mapbox(
        geo_df,
        locations="id",
        featureidkey='properties.id',
        geojson=uk_counties,
        color=color,
        hover_name='county',
        mapbox_style='white-bg',
        color_continuous_scale=px.colors.diverging.Temps_r,
        zoom=3.5,
        center={"lat": 55, "lon": 0},
        animation_frame='date',
        range_color=[-1, 1],
    )
    fig.update_layout(autosize=True, height=900)
    
    return jsonify(fig_to_json(fig))

# Add other API routes as needed...

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)