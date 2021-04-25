import pandas as pd
import time
import numpy as np
from plotly.subplots import make_subplots

from skimage import io
from utils.plotting import format_df_ma_stats, plot_covid_stats, create_event_array, format_df_ma_sent, \
    format_df_ma_tweet_vol, plot_sentiment_vs_volume

from utils.aggregations import aggregate_sentiment_by_region_type_by_date

df_events = pd.read_csv('../data/events/key_events.csv', skipinitialspace=True, usecols=['Date', 'Event'])
start_global = '2020-03-20'
end_global = '2021-03-19'
df_covid_stats = pd.read_csv('../data/COVID-Dataset/uk_covid_stats.csv', skipinitialspace=True)
dates_list = [str(date.date()) for date in pd.date_range(start=start_global, end=end_global).tolist()]

events_array = create_event_array(df_events, start_global, end_global)
all_covid = pd.read_csv('../data/covid/all_tweet_sentiments.csv')
all_lockdown = pd.read_csv('../data/lockdown/all_tweet_sentiments.csv')

# Data Sources
hashtag_data_sources = {'covid': pd.read_csv('../data/covid/top_ten_hashtags_per_day.csv'),
                        'lockdown': pd.read_csv('../data/lockdown/top_ten_hashtags_per_day.csv')}
geo_df_data_sources = {'covid': pd.read_csv('../data/covid/daily_sentiment_county_updated_locations.csv'),
                       'lockdown': pd.read_csv('../data/lockdown/daily_sentiment_county_updated_locations.csv')}

all_sentiment_data_sources = {'covid': all_covid,
                              'lockdown': all_lockdown}
sentiment_dropdown_value_to_avg_score = {'nn': 'nn-predictions_avg_score', 'textblob': 'textblob-predictions_avg_score',
                                         'vader': 'vader-predictions_avg_score'}
sentiment_dropdown_value_to_score = {'nn': 'nn-score', 'textblob': 'textblob-score',
                                     'vader': 'vader-score'}
sentiment_dropdown_value_to_predictions = {'nn': 'nn-predictions', 'textblob': 'textblob-predictions',
                                           'vader': 'vader-predictions'}
tweet_counts_sources = {'covid': pd.read_csv('../data/covid/daily_tweet_count_country.csv'),
                        'lockdown': pd.read_csv('../data/lockdown/daily_tweet_count_country.csv')}
countries = ['England', 'Scotland', 'Northern Ireland', 'Wales']
counties = pd.read_csv('../data/Geojson/uk-district-list-all.csv')['county'].tolist()
regions_lists = {'county': counties, 'country': countries}
# Define frames
import plotly.graph_objects as go

fig = go.Figure(frames=[go.Frame(data=[
    plot_covid_stats(format_df_ma_stats(df_covid_stats, ['England'], start_global, date)
                     , events_array, 'England')[1],
    plot_covid_stats(format_df_ma_stats(df_covid_stats, ['England'], start_global, date)
                     , events_array, 'England')[0]],
    name=str(i)  # you need to name the frame for the animation to behave properly
)
    for i, date in enumerate(dates_list)]
)

fig.add_trace(plot_covid_stats(
    format_df_ma_stats(df_covid_stats, ['England'], start_global, start_global), events_array, 'England')[0]
              )
fig.add_trace(plot_covid_stats(
    format_df_ma_stats(df_covid_stats, ['England'], start_global, start_global), events_array, 'England')[1]
              )

sentiment_data = geo_df_data_sources['lockdown']
agg_data = aggregate_sentiment_by_region_type_by_date(sentiment_data, countries, 'country', start_global,
                                                      end_global)
fig_2 = go.Figure(frames=[go.Frame(data=[
    plot_sentiment_vs_volume(
        format_df_ma_sent(agg_data, 'vader-predictions_avg_score', start_global, date),
        format_df_ma_tweet_vol(tweet_counts_sources['lockdown'], countries, start_global,
                               date),
        'nn-predictions_avg_score', events_array,
        'England')[0],

    plot_sentiment_vs_volume(
        format_df_ma_sent(agg_data, 'vader-predictions_avg_score', start_global, date),
        format_df_ma_tweet_vol(tweet_counts_sources['lockdown'], countries, start_global,
                               date),
        'nn-predictions_avg_score', events_array,
        'Scotland')[0],
    plot_sentiment_vs_volume(
        format_df_ma_sent(agg_data, 'vader-predictions_avg_score', start_global, date),
        format_df_ma_tweet_vol(tweet_counts_sources['lockdown'], countries, start_global,
                               date),
        'nn-predictions_avg_score', events_array,
        'Northern Ireland')[0],
    plot_sentiment_vs_volume(
        format_df_ma_sent(agg_data, 'vader-predictions_avg_score', start_global, date),
        format_df_ma_tweet_vol(tweet_counts_sources['lockdown'], countries, start_global,
                               date),
        'nn-predictions_avg_score', events_array,
        'Wales')[0]

],

    name=str(i)  # you need to name the frame for the animation to behave properly
)
    for i, date in enumerate(dates_list)]
)

fig_2.add_trace(plot_sentiment_vs_volume(
    format_df_ma_sent(agg_data, 'vader-predictions_avg_score', start_global, start_global),
    format_df_ma_tweet_vol(tweet_counts_sources['lockdown'], countries, start_global,
                           start_global),
    'nn-predictions_avg_score', events_array,
    'England')[0])

fig_2.add_trace(plot_sentiment_vs_volume(
    format_df_ma_sent(agg_data, 'vader-predictions_avg_score', start_global, start_global),
    format_df_ma_tweet_vol(tweet_counts_sources['lockdown'], countries, start_global,
                           start_global),
    'nn-predictions_avg_score', events_array,
    'Scotland')[0])

fig_2.add_trace(plot_sentiment_vs_volume(
    format_df_ma_sent(agg_data, 'vader-predictions_avg_score', start_global, start_global),
    format_df_ma_tweet_vol(tweet_counts_sources['lockdown'], countries, start_global,
                           start_global),
    'nn-predictions_avg_score', events_array,
    'Northern Ireland')[0])

fig_2.add_trace(plot_sentiment_vs_volume(
    format_df_ma_sent(agg_data, 'vader-predictions_avg_score', start_global, start_global),
    format_df_ma_tweet_vol(tweet_counts_sources['lockdown'], countries, start_global,
                           start_global),
    'nn-predictions_avg_score', events_array,
    'Wales')[0])

def frame_args(duration):
    return {
        "frame": {"duration": duration},
        "mode": "immediate",
        "fromcurrent": True,
        "transition": {"duration": duration, "easing": "linear"},
    }


sliders = [
    {
        "pad": {"b": 10, "t": 60},
        "len": 0.9,
        "x": 0.1,
        "y": 0,
        "steps": [
            {
                "args": [[f.name], frame_args(0)],
                "label": str(k),
                "method": "animate",
            }
            for k, f in enumerate(fig.frames)
        ],
    }
]

# Layout
fig.update_layout(
    title='Slices in volumetric data',
    width=600,
    height=600,
    scene=dict(
        zaxis=dict(range=[-0.1, 6.8], autorange=False),
        aspectratio=dict(x=1, y=1, z=1),
    ),
    updatemenus=[
        {
            "buttons": [
                {
                    "args": [None, frame_args(50)],
                    "label": "&#9654;",  # play symbol
                    "method": "animate",
                },
                {
                    "args": [[None], frame_args(0)],
                    "label": "&#9724;",  # pause symbol
                    "method": "animate",
                },
            ],
            "direction": "left",
            "pad": {"r": 10, "t": 70},
            "type": "buttons",
            "x": 0.1,
            "y": 0,
        }
    ],
    sliders=sliders
)

fig_2.update_layout(
    title='Slices in volumetric data',
    width=1600,
    height=600,
    scene=dict(
        yaxis=dict(range=[0.2, -0.2], autorange=False),
        aspectratio=dict(x=1, y=1, z=1),
    ),
    updatemenus=[
        {
            "buttons": [
                {
                    "args": [None, frame_args(50)],
                    "label": "&#9654;",  # play symbol
                    "method": "animate",
                },
                {
                    "args": [[None], frame_args(0)],
                    "label": "&#9724;",  # pause symbol
                    "method": "animate",
                },
            ],
            "direction": "left",
            "pad": {"r": 10, "t": 70},
            "type": "buttons",
            "x": 0.1,
            "y": 0,
        }
    ],
    sliders=sliders,
    yaxis_range=[-0.35, 0.35]

)
# fig.show()
fig_2.show()
import time
import numpy as np
