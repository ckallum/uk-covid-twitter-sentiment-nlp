"""
API backend for COVID-19 Sentiment Dashboard
"""
import json
import re
import os
import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from flask import Flask, jsonify, request, send_from_directory

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

app = Flask(__name__, static_folder="static")

# READ DATA
df_covid_stats = pd.read_csv(
    'data/covid-data/uk_covid_stats.csv', skipinitialspace=True)
uk_counties = json.load(open('data/geojson/uk_counties_simpler.json', 'r'))
r_numbers = pd.read_csv('data/covid-data/r_numbers.csv')
df_events = pd.read_csv('data/events/key_events.csv',
                        skipinitialspace=True, usecols=['Date', 'Event'])
counties = pd.read_csv(
    'data/geojson/uk-district-list-all.csv')['county'].tolist()
hashtags_covid = pd.read_csv('data/covid/top_ten_hashtags_per_day.csv')
hashtags_lockdown = pd.read_csv('data/lockdown/top_ten_hashtags_per_day.csv')
geo_df_covid = pd.read_csv(
    'data/covid/daily_sentiment_county_updated_locations.csv')
geo_df_lockdown = pd.read_csv(
    'data/lockdown/daily_sentiment_county_updated_locations.csv')
tweet_count_covid = pd.read_csv('data/covid/daily_tweet_count_country.csv')
tweet_count_lockdown = pd.read_csv(
    'data/lockdown/daily_tweet_count_country.csv')
all_sentiments_covid = pd.read_csv('data/covid/all_tweet_sentiments.csv')
all_sentiments_lockdown = pd.read_csv('data/lockdown/all_tweet_sentiments.csv')
notable_days_covid = pd.read_csv('data/covid/notable_days_months.csv')
notable_days_lockdown = pd.read_csv('data/lockdown/notable_days_months.csv')
scatter_covid = pd.read_csv('data/covid/scatter.csv')
scatter_lockdown = pd.read_csv('data/lockdown/scatter.csv')

emojis_covid = pd.read_csv('data/covid/weekly_emojis_with_colours.csv')
emojis_lockdown = pd.read_csv('data/lockdown/weekly_emojis_with_colours.csv')
news_df = pd.read_csv('data/events/news_timeline.csv')

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
# Formatted
formatted_tweet_count = {'covid': format_df_ma_tweet_vol(tweet_count_covid, countries),
                         'lockdown': format_df_ma_tweet_vol(tweet_count_lockdown, countries)}
formatted_tweet_sent = {'covid': format_df_ma_sent(
    geo_df_covid), 'lockdown': format_df_ma_sent(geo_df_lockdown)}

formatted_covid_stats = format_df_ma_stats(df_covid_stats, countries)

formatted_sent_comp = {'covid': format_df_ma_sent_comp(all_sentiments_covid),
                       'lockdown': format_df_ma_sent_comp(all_sentiments_lockdown)}

emojis_weekly_source = {'covid': emojis_covid, 'lockdown': emojis_lockdown}

# Dates
weeks = r_numbers['date'].tolist()
week_pairs = [(weeks[i], weeks[i + 1]) for i in range(0, len(weeks) - 1)]
start_global = '2020-03-20'
end_global = '2021-03-25'
dates_list = pd.date_range(start=start_global, end=end_global)
str_dates_list = [str(date.date()) for date in dates_list]

# Events
events_array = create_event_array(df_events, start_global, end_global)

def check_between_dates(start, end, current):
    start, end, current = pd.to_datetime(start, format='%d/%m/%Y'), \
                          pd.to_datetime(end, format='%d/%m/%Y'), \
                          pd.to_datetime(current, format='%Y-%m-%d')
    return start < current <= end

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

# Serve static files from the static directory
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

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

@app.route('/api/sentiment_bar_chart')
def get_sentiment_bar_chart():
    """Get sentiment bar chart data"""
    date = request.args.get('date')
    source = request.args.get('source', 'covid')
    nlp_type = request.args.get('nlp_type', 'vader')
    
    data = complete_data_sources[source]
    data['date'] = pd.to_datetime(data['date']).dt.date
    df = data[data['date'] == datetime.datetime.strptime(date, '%Y-%m-%d').date()]
    label = sentiment_dropdown_value_to_predictions[nlp_type]
    
    fig = plot_sentiment_bar(df, label, countries)
    
    return jsonify(fig_to_json(fig))

@app.route('/api/emoji_bar_chart')
def get_emoji_bar_chart():
    """Get emoji bar chart data"""
    date = request.args.get('date')
    topic = request.args.get('topic', 'covid')
    
    # Adjust to get the weekly start date
    date_obj = datetime.datetime.strptime(date, '%Y-%m-%d')
    date_index = (dates_list == date_obj).argmax()
    weekly_index = date_index - (date_index % 7)
    weekly_date = str(dates_list[weekly_index].date())
    
    emoji_df = emojis_weekly_source[topic]
    fig = plot_emoji_bar_chart(emoji_df, weekly_date)
    
    return jsonify(fig_to_json(fig))

@app.route('/api/hashtag_table')
def get_hashtag_table():
    """Get hashtag table data"""
    date = request.args.get('date')
    source = request.args.get('source', 'covid')
    
    hashtags_df = hashtag_data_sources[source]
    hashtag_date = hashtags_df.loc[hashtags_df['date'] == date]
    
    if hashtag_date.empty:
        return jsonify({
            'data': [],
            'layout': {'title': 'No data available for this date'}
        })
    
    hashtags = [tuple(x.split(',')) for x in re.findall(
        "\((.*?)\)", hashtag_date['top_ten_hashtags'].values[0])]
    hash_dict = {'Hashtag': [], 'Count': []}
    for hashtag, count in hashtags:
        hash_dict['Hashtag'].append('#' + hashtag.replace("'", ''))
        hash_dict['Count'].append(int(count))
    hash_df = pd.DataFrame(hash_dict)
    
    fig = plot_hashtag_table(hash_df)
    
    return jsonify(fig_to_json(fig))

@app.route('/api/daily_news')
def get_daily_news():
    """Get daily news content"""
    date = request.args.get('date')
    
    df = news_df.loc[news_df['Date'] == date]
    links = ''
    for ind in df.index:
        headline = news_df['Headline'][ind]
        URL = df['URL'][ind]
        link = f'<a href="{URL}" target="_blank"><b>{headline}</b></a><br><br>'
        links += link
    
    return jsonify({
        'date': date,
        'content': links
    })

@app.route('/api/stats_graph')
def get_stats_graph():
    """Get COVID stats graph"""
    date = request.args.get('date')
    
    fig = plot_covid_stats(formatted_covid_stats, countries, events_array, start_global, date)
    
    return jsonify(fig_to_json(fig))

@app.route('/api/ma_sent_graph')
def get_ma_sent_graph():
    """Get moving average sentiment graph"""
    date = request.args.get('date')
    topic = request.args.get('topic', 'covid')
    sentiment_type = request.args.get('sentiment_type', 'vader')
    
    sentiment_col = sentiment_dropdown_value_to_avg_score[sentiment_type]
    tweet_sent_df = formatted_tweet_sent[topic]
    
    fig = plot_sentiment(tweet_sent_df, sentiment_col, start_global, date)
    
    return jsonify(fig_to_json(fig))

@app.route('/api/notable_days')
def get_notable_days():
    """Get notable days table"""
    topic = request.args.get('topic', 'covid')
    nlp_type = request.args.get('nlp_type', 'vader')
    
    source = notable_days_sources[topic]
    df = source.loc[source['sentiment_type'] == nlp_type]
    
    fig = plot_notable_days(df)
    
    return jsonify(fig_to_json(fig))

@app.route('/api/dropdown_figure')
def get_dropdown_figure():
    """Get dropdown figure based on selected options"""
    topic = request.args.get('topic', 'covid')
    sentiment_type = request.args.get('sentiment_type', 'vader')
    chart_value = request.args.get('chart_value', 'show_sentiment_comparison')
    
    selected_date = end_global
    sentiment_col = sentiment_dropdown_value_to_avg_score[sentiment_type]
    tweet_count_df = formatted_tweet_count[topic]
    tweet_sent_df = formatted_tweet_sent[topic]
    
    if chart_value == 'show_sentiment_vs_time':
        fig = plot_dropdown_sent_vs_vol(
            tweet_sent_df, tweet_count_df, sentiment_col, events_array, countries, start_global, selected_date
        )
    elif chart_value == 'show_sentiment_comparison':
        df = formatted_sent_comp[topic]
        fig = plot_sentiment_comp(df, start_global, selected_date)
    else:
        return jsonify({
            'error': 'Invalid chart type'
        })
    
    return jsonify(fig_to_json(fig))

@app.route('/api/corr_mat')
def get_corr_mat():
    """Get correlation matrix"""
    topic = request.args.get('topic', 'covid')
    sentiment_type = request.args.get('sentiment_type', 'vader')
    
    sentiment_col = sentiment_dropdown_value_to_avg_score[sentiment_type]
    data = scatter_sources[topic]
    
    fig = plot_corr_mat(data, sentiment_col)
    
    return jsonify(fig_to_json(fig))

if __name__ == '__main__':
    # Get port from environment variable (for Heroku compatibility)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)