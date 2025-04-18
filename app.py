import json
import re
import time
import datetime
import os
from pathlib import Path
# import dash_bootstrap_components as dbc
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash.dependencies import Input, Output, State

from utils.formatting import create_event_array
from utils.formatting import format_df_ma_stats, format_df_ma_sent, format_df_ma_tweet_vol, format_df_corr, \
    format_df_notable_days, format_df_ma_sent_comp

from utils.plotting import plot_dropdown_sent_vs_vol, plot_covid_stats, plot_hashtag_table, \
    plot_sentiment, plot_corr_mat, plot_sentiment_bar, plot_emoji_bar_chart, emoji_to_colour, \
    plot_notable_days, plot_sentiment_comp

# Define the base directory using pathlib for cross-platform compatibility
BASE_DIR = Path(__file__).resolve().parent

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


server = app.server
app.title = 'Sentiment Towards COVID-19 in the UK'
app.config.suppress_callback_exceptions = True
# READ DATA
df_covid_stats = pd.read_csv(
    BASE_DIR / 'data/covid-data/uk_covid_stats.csv', skipinitialspace=True)
uk_counties = json.load(open(BASE_DIR / 'data/geojson/uk_counties_simpler.json', 'r'))
r_numbers = pd.read_csv(BASE_DIR / 'data/covid-data/r_numbers.csv')
df_events = pd.read_csv(BASE_DIR / 'data/events/key_events.csv',
                        skipinitialspace=True, usecols=['Date', 'Event'])
counties = pd.read_csv(
    BASE_DIR / 'data/geojson/uk-district-list-all.csv')['county'].tolist()
hashtags_covid = pd.read_csv(BASE_DIR / 'data/covid/top_ten_hashtags_per_day.csv')
hashtags_lockdown = pd.read_csv(BASE_DIR / 'data/lockdown/top_ten_hashtags_per_day.csv')
geo_df_covid = pd.read_csv(
    BASE_DIR / 'data/covid/daily_sentiment_county_updated_locations.csv')
geo_df_lockdown = pd.read_csv(
    BASE_DIR / 'data/lockdown/daily_sentiment_county_updated_locations.csv')
tweet_count_covid = pd.read_csv(BASE_DIR / 'data/covid/daily_tweet_count_country.csv')
tweet_count_lockdown = pd.read_csv(
    BASE_DIR / 'data/lockdown/daily_tweet_count_country.csv')
all_sentiments_covid = pd.read_csv(BASE_DIR / 'data/covid/all_tweet_sentiments.csv')
all_sentiments_lockdown = pd.read_csv(BASE_DIR / 'data/lockdown/all_tweet_sentiments.csv')
notable_days_covid = pd.read_csv(BASE_DIR / 'data/covid/notable_days_months.csv')
notable_days_lockdown = pd.read_csv(BASE_DIR / 'data/lockdown/notable_days_months.csv')
scatter_covid = pd.read_csv(BASE_DIR / 'data/covid/scatter.csv')
scatter_lockdown = pd.read_csv(BASE_DIR / 'data/lockdown/scatter.csv')

emojis_covid = pd.read_csv(BASE_DIR / 'data/covid/weekly_emojis_with_colours.csv')
emojis_lockdown = pd.read_csv(BASE_DIR / 'data/lockdown/weekly_emojis_with_colours.csv')
news_df = pd.read_csv(BASE_DIR / 'data/events/news_timeline.csv')

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

#
events_array = create_event_array(df_events, start_global, end_global)

# Initial map
covid_geo_df = geo_df_data_sources['covid'].loc[geo_df_data_sources['covid']
                                                ['date'] == start_global]
fig_0 = px.choropleth_mapbox(
    covid_geo_df,
    locations="id",
    featureidkey='properties.id',
    geojson=uk_counties,
    color=sentiment_dropdown_value_to_avg_score['nn'],
    hover_name='county',
    mapbox_style='white-bg',
    color_continuous_scale=px.colors.diverging.Temps_r,
    zoom=3.5,
    center={"lat": 55, "lon": 0},
    animation_frame='date',
    range_color=[-1, 1],
)

emoji_covid_fig = plot_emoji_bar_chart(emojis_covid, start_global)


def check_between_dates(start, end, current):
    start, end, current = pd.to_datetime(start, format='%d/%m/%Y'), \
                          pd.to_datetime(end, format='%d/%m/%Y'), \
                          pd.to_datetime(current, format='%Y-%m-%d')
    return start < current <= end


def indicator(color, text, id_value):
    return html.Div(
        [
            html.P(
                children=text,
                className="info_text"
            ),
            html.H4(
                id=id_value,
                className="indicator_value"),
        ],
        className="pretty_container three columns",

    )


def covid_stats_indicators():
    return html.Div(
        [
            indicator("#00cc96", "Total Deaths", "total_deaths_indicator"),
            indicator(
                "#119DFF", "Total Cases", "total_cases_indicator"
            ),
            indicator("#EF553B", "R-Number", "r_number_indicator"),
            indicator(None, 'Current Date', 'current_date_indicator')
        ],
        className="twelve columns"
    )


def filters():
    return html.Div(
        [
            html.Div(children=[
                html.P(id='df-selected', children='Select Tweet Data-set '),
                dcc.Dropdown(
                    id="source-dropdown",
                    options=[
                        {"label": "COVID", "value": "covid"},
                        {"label": "Lockdown", "value": "lockdown"}
                    ],
                    value="covid",
                    clearable=False,
                )],
                className="pretty_container three columns",
            ),
            html.Div(children=[
                html.P(id='nlp-selected', children='Select NLP Technique'),
                dcc.Dropdown(
                    id="nlp-dropdown",
                    options=[
                        {"label": "Vader", "value": "vader"},
                        {"label": "Text Blob", "value": "textblob"},
                        {"label": "LSTM", "value": "nn"},
                        {"label": 'Naive Bayes', "value": 'native'}
                    ],
                    value="vader",
                    clearable=False,
                )],
                className="pretty_container three columns",
            )
        ],
        className="eight columns",
        style={"margin-bottom": "10px"},
    )


# the style arguments for the sidebar. We use position:fixed and a fixed width
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 62.5,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "height": "40%",
    "z-index": 1,
    "overflow-x": "hidden",
    "transition": "all 0.5s",
    "padding": "0.5rem 1rem",
    "background-color": "#f8f9fa",
}

CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

sidebar = html.Div(
    [
        html.H2("Sidebar", className="display-4"),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink("Home\n\n", href="/", active="exact"),
                html.Br(),
                html.Br(),
                dbc.NavLink("Timeline Exploration,\n\n", href="/page-1", active="exact"),
                html.Br(),
                html.Br(),
                dbc.NavLink("Data Analysis,\n\n", href="/page-2", active="exact"),
            ],
            vertical='md',
            pills=True,
        ),
    ],
    style=SIDEBAR_STYLE,
)

content = html.Div(id="page-content", style=CONTENT_STYLE)

app.layout = html.Div([dcc.Location(id="url"), sidebar, content])

#  App Layout
layout_main = [
    html.Div(
        id="app-container",
        children=[dcc.Interval(
            id="interval-component",
            interval=2 * 1000,  # in milliseconds
            n_intervals=0,  # start at batch 50
            disabled=True,
        ),
            dcc.Loading(html.Div(id='scatter-loading'),
                        loading_state={
                            'component_name': 'app-container', 'is_loading': True},
                        fullscreen=True, type='graph'),
            html.Div(
                children=[
                    html.Div(
                        id="analysis-header",
                        children=[
                            html.H2(
                                children='Timeline Exploration'
                            ),
                        ],
                        className='pretty_container twelve columns'
                    )
                ],
                className='row'
            ),
            html.Div(children=[
                filters(),
                covid_stats_indicators()],
                className='row'),
            html.Div(children=[
                html.Div(
                    id='button-container',
                    children=[
                        html.Button(
                            'Previous Date', id='prev-button', n_clicks=0
                        ),
                        html.Button(
                            'Next Date', id='next-button', n_clicks=0
                        ),
                        html.Button(
                            'Play', id='play-button', n_clicks=0
                        )
                    ]
                )
            ],
                className='row'),
            html.Div(children=[
                html.Div(
                    id="slider-container",
                    children=[
                        html.P(
                            id="slider-text",
                            children="Drag the slider to change the date:",
                        ),
                        dcc.Slider(
                            id="days-slider",
                            min=0,
                            max=364,
                            value=0,
                            marks={
                                str(x): {
                                    "label": dates_list[x].date()
                                }
                                for x in range(0, 364, 30)
                            },
                        ),
                    ],
                    className='pretty_container twelve columns'
                )],
                className='row'),
            html.Div(
                id='toggle-container',
                children=[

                    html.Div(
                        dcc.Checklist(
                            id='heatmap-container-toggle',
                            options=[
                                {'label': 'Sentiment Heatmap',
                                 'value': 'on'},
                            ],
                            value=['on'],
                        ),
                        style={'padding': '5px', 'display': 'inline-block'},
                    ),

                    html.Div(
                        dcc.Checklist(
                            id='bar_chart_div-toggle',
                            options=[
                                {'label': 'Sentiment and Emoji Bar Charts',
                                 'value': 'on'},
                            ],
                            value=['on'],
                        ),
                        style={'padding': '5px', 'display': 'inline-block'},
                    ),

                    html.Div(
                        dcc.Checklist(
                            id='news-hashtag-div-toggle',
                            options=[
                                {'label': 'News and Hashtags',
                                 'value': 'on'},
                            ],
                            value=['on'],
                        ),
                        style={'display': 'inline-block'},
                    ),

                    html.Div(
                        dcc.Checklist(
                            id='deaths-and-cases-div-toggle',
                            options=[
                                {'label': 'Deaths and Cases',
                                 'value': 'on'},
                            ],
                            value=['on'],
                        ),
                        style={'padding': '5px', 'display': 'inline-block'},
                    ),

                    html.Div(
                        dcc.Checklist(
                            id='7-day-MA-div-toggle',
                            options=[
                                {'label': '7 Day Moving Average',
                                 'value': 'on'},
                            ],
                            value=['on'],
                        ),
                        style={'padding': '5px', 'display': 'inline-block'},
                    ),

                ],
                className='pretty_container'
            ),
            html.Div(children=[
                html.Div(
                    id="left-column",
                    children=[
                        html.Div(
                            id="heatmap-container",
                            children=[
                                html.H6(
                                    "Heatmap of sentiment towards COVID-19 in the UK on day: ",
                                    id="heatmap-title",
                                ),
                                dcc.Graph(
                                    id='county-choropleth',
                                    figure=fig_0
                                ),
                            ],
                        ),
                    ],
                    className='pretty_container five columns'
                ),

                html.Div(
                    id='bar_chart_div',
                    children=[
                        html.Div(
                            id="bar-chart-container",
                            children=[

                                html.Div(children=[
                                    html.H6(
                                        children='Sentiment Count Per Day'
                                    ),
                                    dcc.Checklist(
                                        id='sentiment_bar_chart_toggle',
                                        options=[
                                            {'label': 'Show/Hide',
                                             'value': 'on'},
                                        ],
                                        value=['on']
                                    ),

                                    dcc.Graph(
                                        id='sentiment_bar_chart'
                                    ),
                                    html.H6(
                                        "Top Weekly Emojis",
                                    ),
                                    dcc.Checklist(
                                        id='emoji-bar-chart-toggle',
                                        options=[
                                            {'label': 'Show/Hide',
                                             'value': 'on'},
                                        ],
                                        value=['on']
                                    ),
                                    dcc.Graph(
                                        id='emoji-bar-chart',
                                        figure=emoji_covid_fig
                                    )
                                ],
                                    className='pretty_container twelve columns'
                                )
                            ],
                            className='row'

                        ),
                    ],
                    className='pretty_container four columns'
                ),
                html.Div(
                    id='news-hashtag-div',
                    children=[
                        html.Div(
                            children=[
                                html.Div(children=[
                                    html.H6(
                                        "Top News Stories",
                                    ),
                                    html.H6(
                                        style={
                                            "color": "#2a3f5f",
                                            "fontSize": "13px",
                                            "textAlign": "center",
                                            "marginBottom": "50",
                                        },
                                    ),
                                    dcc.Checklist(
                                        id='daily-news-toggle',
                                        options=[
                                            {'label': 'Show/Hide',
                                             'value': 'on'},
                                        ],
                                        value=['on']
                                    ),
                                    dcc.Markdown(
                                        id="daily-news",
                                        style={
                                            "padding": "10px 13px 5px 13px", "marginBottom": "5"},
                                    ),
                                    html.H6(
                                        "Top 10 Hashtags",
                                    ),
                                    dcc.Checklist(
                                        id='hashtag-table-toggle',
                                        options=[
                                            {'label': 'Show/Hide',
                                             'value': 'on'},
                                        ],
                                        value=['on']
                                    ),
                                    dcc.Graph(
                                        id='hashtag-table'
                                    ),
                                ],
                                    className='pretty_container twelve columns'

                                ),

                            ],
                            className='row'
                        )

                    ],
                    className="pretty_container four columns",
                ),

            ],
                className='row'
            ),
            html.Div(
                id='covid-stats',
                children=[
                    html.Div(
                        id="covid-stats-container",
                        children=[
                            html.H6(
                                "Deaths and Cases Over Time",
                                id="stats-title",
                            ),
                            dcc.Graph(
                                id='stats-graph'
                            ),
                        ],
                        className='pretty_container six columns'

                    ),
                    html.Div(
                        id="ma-sent-container",
                        children=[
                            html.H6(
                                "7 Day Moving Average of Covid Sentiment For Each Country\n(Starts at 2020-03-27)",
                                id="sent-vol-title",
                            ),
                            dcc.Graph(
                                id='ma-sent-graph'
                            ),
                        ],
                        className='pretty_container six columns'

                    )
                ],
                className='row',
                style={'height': '850px'}

            ),
        ]
    )
]

layout_analysis = [
    dcc.Loading(html.Div(id='scatter-loading'),
                loading_state={
                    'component_name': 'app-container', 'is_loading': True},
                fullscreen=True, type='graph'),
    html.Div(
        children=[
            html.Div(
                id="analysis-header",
                children=[
                    html.H2(
                        children='Data Analysis and Exploration'
                    ),
                ],
                className='pretty_container twelve columns'
            )
        ],
        className='row'
    ),
    html.Div(children=[
        filters(),
    ],
        className='row'),
    html.Div(children=[
        html.H6(
            "Notable Days",
        ),
        dcc.Graph(
            id='notable-day-table'
        ),
    ],
        className='pretty_container four columns'
    ),
    html.Div(children=[
        html.Div(
            id="graph-container",
            children=[
                html.P(id="chart-selector",
                       children="Select Chart:"),
                dcc.Dropdown(
                    options=[

                        {
                            "label": "7 Day MA COVID Sentiment vs Tweet Volume (Starts at 2020-03-27)",
                            "value": "show_sentiment_vs_time",
                        },

                        {
                            "label": "Comparison of Sentiment Generation Techniques (Starts at 2020-03-27)",
                            "value": "show_sentiment_comparison",
                        },
                    ],
                    value="show_sentiment_comparison",
                    id="chart-dropdown",
                ),
                dcc.Graph(
                    id='dropdown-figure'
                ),
            ],
            className='pretty_container twelve columns'
        ),
    ],
        className='row'
    ),
    html.Div(
        children=[
            html.Div(
                id='emoji-wordcloud-div',
                children=[
                    html.H4(
                        children="Popular Emoji's"
                    ),
                    html.Img(
                        id='emoji-wordcloud',
                        src=app.get_asset_url(
                            'covid_emoji_wordcloud.png'),
                        style={
                            'height': '200px',
                            'width': '90%'
                        }),
                    html.H4(
                        children="Popular Words's(Excluding Keywords)"
                    ),
                    html.Img(
                        id='wordcloud',
                        src=app.get_asset_url(
                            'covid_wordcloud.png'),
                        style={
                            'height': '200px',
                            'width': '90%'
                        })
                ],
                className='pretty_container four columns'
            ),
            html.Div(
                children=[
                    html.H4(
                        children=[
                            'Correlation Between Features(Scaled Volume, Deaths, Cases)',
                            dcc.Graph(
                                id='corr-mat'
                            ),
                        ]
                    )

                ],
                className='pretty_container eight columns'
            )
        ],
        className='row'
    )]

layout_faq = [
    html.Div(children=[
        dcc.Loading(html.Div(id='scatter-loading'),
                    loading_state={
                        'component_name': 'app-container', 'is_loading': True},
                    fullscreen=True, type='graph'),
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.H4(
                            "About this Dashboard",
                        ),
                        dcc.Markdown('''
                        
                        The  Coronavirus  (COVID-19)  pandemic  has  been at the forefront 
                        of the global population’s concerns over the last year with the consequence 
                        having a large impact on individuals daily  lives.  Twitter  is  one  of  the  largest 
                         social  media  platforms where  people  from  all  over  the  country(and  the  world)  
                         express their  opinions  regarding  a  wide  range  of  topics,  and  it  is  of
                         no  surprise  that  there  has  been  a  surge  of  discussion  around
                         pandemic  and  pandemic  adjacent  topics.
                         
                         The focus of this analysis is on ’tweet’s   posted   within   the   United
                         Kingdom with the aim to measure the pulse of general sentiment
                         towards COVID and lockdown over the past year. A multitude of sentiment analysis 
                         techniques are applied to the data to measure sentiment  change  over  time.
                         
                         This dashboard  provides insight  and  visualises  the  change  in  language  expression  over  a year.
                          Specifically, exploring reactions to relevant events combined with  COVID  statistics  
                          within  the  UK.  Ultimately, with the aim  to make exploration and analysis of our
                           data easily accessible to a nontechnical audience.
                            
                         The end-user will be able to compare the results of different sentiment techniques and how public opinion compares between 
                          countries/regions in relation to the number of deaths, the number of cases, and certain pandemic related news events  over  the  last  year.
                           
                           **Please use the sidebar to navigate to the rest of the dashboard!**
                           
                           Have fun :)!
                        
                        ''')

                    ],
                ),
            ],
            className='pretty_container five columns'
        ),

        html.Div(
            id='bar_chart_div',
            children=[
                html.Div(
                    id="bar-chart-container",
                    children=[

                        html.Div(children=[
                            html.H4(
                                children='Data Collected'
                            ),
                            dcc.Markdown(
                                '''
                                This dashboard contains two datasets corresponding to COVID and lockdown 
                                related Tweets posted within the United Kingdom.
                                
                                Each dataset contains approximately 300 thousand tweets, starting from
                                 the 20 March 2020 to the 25 March 2021.
                                
                                The keywords used to scrape the COVID dataset include:
                                "coronavirus OR covid OR covid19 OR covid-19"
                                
                                The keyword used to scrape the lockdown dataset include:
                                "lockdown"
                                
                                I used [SNScrape](https://github.com/JustAnotherArchivist/snscrape/tree/master/snscrape)
                                , an open source wrapper of the Twitter API to collect historical 
                                Tweets within the UK containing our key words over the past year.
                                
                                See Twitter's Developer Policy regarding API and content usage 
                                [here](https://developer.twitter.com/en/developer-terms/agreement-and-policy).
                                
                                The news events were collected from the [Guardian News API](https://open-platform.theguardian.com/)
                                
                                The relavant COVID statistics were collected from the [Public Health England](https://coronavirus.data.gov.uk/)
                                '''

                            ),

                            html.H4(
                                "Sentiment Techniques",
                            ),
                            dcc.Markdown(
                                '''
                                This dashboard analyses and compares sentiment of tweet content using four 
                                sentiment generating techniques:
                                
                                [Vader](https://github.com/cjhutto/vaderSentiment)
                                
                                [Naive Bayes](https://web.stanford.edu/~jurafsky/slp3/4.pdf)
                                
                                [LSTM](https://www.aclweb.org/anthology/O18-1021.pdf)
                                
                                [Textblob](https://github.com/sloria/TextBlob)
                                
                                
                                '''

                            ),
                        ],
                            className='pretty_container twelve columns'
                        )
                    ],
                    className='row'

                ),
            ],
            className='pretty_container five columns'
        ),
        html.Div(
            id='news-hashtag-div',
            children=[
                html.Div(
                    children=[
                        html.Div(children=[
                            html.H4(
                                "About the Creator",
                            ),

                            dcc.Markdown('''
                            This was a project to understand(prove a point) about how certain event's shifted sentiment(across Twitter) over different georgraphic and political UK counties during COVID.
                            
                            ''')
                        ],
                            className='pretty_container twelve columns'

                        ),

                    ],
                    className='row'
                )

            ],
            className="pretty_container three columns",
        ),

    ],
        className='row'
    ),
]


@app.callback(Output('r_number_indicator', 'children'), [Input("days-slider", "value")])
def update_r_text(date_index):
    selected_date = str(dates_list[date_index].date())
    for i, (start, end) in enumerate(week_pairs):
        if check_between_dates(start, end, selected_date):
            df = r_numbers.loc[r_numbers['date'] == start]
            # Fix dtype incompatibility by properly accessing Series elements
            upper = df['upper'].iloc[0] if not df['upper'].empty else 0
            lower = df['lower'].iloc[0] if not df['lower'].empty else 0
            avg_r = round((upper + lower) / 2, 2)
            if avg_r == 0:
                return 'N/A'
            return "~{}".format(avg_r)
    return 'N/A'


@app.callback(Output('total_cases_indicator', 'children'), [Input("days-slider", "value")])
def update_cases_text(date_index):
    selected_date = str(dates_list[date_index].date())
    cases = df_covid_stats.loc[df_covid_stats['date']
                               == selected_date, 'cumCasesByPublishDate'].sum()
    return cases


@app.callback(Output('total_deaths_indicator', 'children'), [Input("days-slider", "value")])
def update_deaths_text(date_index):
    selected_date = str(dates_list[date_index].date())
    deaths = df_covid_stats.loc[df_covid_stats['date']
                                == selected_date, 'cumDeathsByDeathDate'].sum()
    return deaths


@app.callback(Output("current_date_indicator", "children"), [Input("days-slider", "value")])
def update_date_box(selected_date):
    return dates_list[selected_date].date()


@app.callback(Output("heatmap-title", "children"), [Input("days-slider", "value"), Input('source-dropdown', 'value')])
def update_map_title(selected_date, source):
    return "Heatmap of Sentiment Within {} Related Tweets in the UK. Date: {}".format(source,
                                                                                      dates_list[
                                                                                          selected_date].date()
                                                                                      )


@app.callback(
    Output('sentiment_bar_chart', 'figure'),
    [Input("days-slider", "value"), Input('source-dropdown',
                                          'value'), Input('nlp-dropdown', 'value')]
)
def update_bar_chart(selected_date, source, nlp):
    data = complete_data_sources[source]
    data['date'] = pd.to_datetime(data['date']).dt.date
    df = data[data['date'] == dates_list[selected_date]]
    label = sentiment_dropdown_value_to_predictions[nlp]
    return plot_sentiment_bar(df, label, countries)


#
@app.callback(
    Output('hashtag-table', 'figure'),
    [Input("days-slider", "value"), Input('source-dropdown', 'value')]
)
def update_hashtag_table(selected_date, source):
    selected_date = str(dates_list[selected_date].date())
    hashtags_df = hashtag_data_sources[source]
    hashtag_date = hashtags_df.loc[hashtags_df['date'] == selected_date]
    hashtags = [tuple(x.split(',')) for x in re.findall(
        "\((.*?)\)", hashtag_date['top_ten_hashtags'].values[0])]
    hash_dict = {'Hashtag': [], 'Count': []}
    for hashtag, count in hashtags:
        hash_dict['Hashtag'].append('#' + hashtag.replace("'", ''))
        hash_dict['Count'].append(int(count))
    hash_df = pd.DataFrame(hash_dict)
    return plot_hashtag_table(hash_df)


@app.callback(
    [Output('interval-component', 'n_intervals'), Output('interval-component', 'disabled'),
     Output('play-button', 'children')],
    [Input('next-button', 'n_clicks'), Input('prev-button', 'n_clicks'), Input('play-button', 'n_clicks'),
     State('days-slider', 'value'), State('interval-component', 'disabled'), State('play-button', 'children')]
)
def button_pressed(inc_btn, dec_btn, play_btn, day, disabled, play_text):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if 'next-button' in changed_id and disabled:
        if day < 364:
            return day, disabled, play_text
    if 'prev-button' in changed_id and disabled:
        if day > 0:
            return day - 2, disabled, play_text
    if 'play-button' in changed_id:
        if disabled:
            return day, not disabled, 'stop'
        else:
            return day, True, 'start'

    return day - 1, True, play_text


@app.callback(Output("days-slider", "value"),
              [Input('interval-component', 'n_intervals')])
def update_interval(current_interval):
    if current_interval < 364:
        return current_interval + 1


@app.callback(
    Output("county-choropleth", "figure"),
    [Input("days-slider", "value"), Input("nlp-dropdown", "value"),
     Input("source-dropdown", "value")

     ]
)
def display_map(day, nlp, topic):
    geo_df = geo_df_data_sources[topic]
    color = sentiment_dropdown_value_to_avg_score[nlp]
    # Initial map
    date = str(dates_list[day].date())
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
    return fig


@app.callback(
    Output("stats-graph", "figure"),
    [Input("days-slider", "value")
     ]
)
def display_stats(day):
    today = str(dates_list[day].date())
    return plot_covid_stats(formatted_covid_stats, countries, events_array, start_global, today)


@app.callback(
    Output('ma-sent-graph', 'figure'),
    [Input("days-slider", "value"), Input('source-dropdown',
                                          'value'), Input('nlp-dropdown', 'value')]
)
def display_sentiments(day, topic, sentiment_type):
    selected_date = str(dates_list[day].date())
    sentiment_col = sentiment_dropdown_value_to_avg_score[sentiment_type]
    tweet_sent_df = formatted_tweet_sent[topic]
    # tweet_sent_df = formatted_scaled_sent[topic]
    return plot_sentiment(tweet_sent_df, sentiment_col, start_global, selected_date)


@app.callback(
    Output("daily-news", "children"),
    [Input("days-slider", "value")],
)
def display_news(day):
    date = str(dates_list[day].date())
    df = news_df.loc[news_df['Date'] == date]
    # news_fig = ff.create_table(news_df.drop('Date', 1))
    # return df_to_table(news_df)
    links = ''
    for ind in df.index:
        headline = news_df['Headline'][ind]
        URL = df['URL'][ind]
        link = '[**' + headline + '**](' + URL + ') '
        blank = '''

        '''
        links = links + blank + link
    return (links)


@app.callback(
    Output('dropdown-figure', 'figure'),
    [Input('source-dropdown', 'value'), Input('nlp-dropdown', 'value'),
     Input('chart-dropdown', 'value')]
)
def dropdown_chart(topic, sentiment_type, chart_value):
    selected_date = end_global
    sentiment_col = sentiment_dropdown_value_to_avg_score[sentiment_type]
    tweet_count_df = formatted_tweet_count[topic]
    tweet_sent_df = formatted_tweet_sent[topic]

    if chart_value == 'show_sentiment_vs_time':
        return plot_dropdown_sent_vs_vol(tweet_sent_df, tweet_count_df, sentiment_col, events_array, countries,
                                         start_global,
                                         selected_date)
    if chart_value == 'show_sentiment_comparison':
        df = formatted_sent_comp[topic]
        return plot_sentiment_comp(df, start_global, selected_date)
    return None


@app.callback(
    Output('corr-mat', 'figure'),
    [Input('source-dropdown', 'value'), Input('nlp-dropdown', 'value')]
)
def correlation_matrix(topic, sentiment_type):
    sentiment_col = sentiment_dropdown_value_to_avg_score[sentiment_type]
    data = scatter_sources[topic]
    fig = plot_corr_mat(data, sentiment_col)
    return fig


@app.callback(
    Output('emoji-bar-chart', 'figure'),
    [Input("days-slider", "value"), Input('source-dropdown', 'value')]
)
def update_emoji_bar_chart(selected_date, topic):
    selected_date = selected_date - (selected_date % 7)
    date = str(dates_list[selected_date].date())
    emoji_df = emojis_weekly_source[topic]
    return plot_emoji_bar_chart(emoji_df, date)


# Loading Spinners
@app.callback(Output('scatter-loading', 'children'), [Input('page-content', 'children')])
def load(figure):
    time.sleep(2.5)
    return None


@app.callback(Output('notable-day-table', 'figure'),
              [Input('source-dropdown', 'value'), Input('nlp-dropdown', 'value')])
def notable_days(topic, col):
    source = notable_days_sources[topic]
    df = source.loc[source['sentiment_type'] == col]
    fig = plot_notable_days(df)
    return fig


@app.callback(Output('emoji-wordcloud', 'src'),
              Input('source-dropdown', 'value'))
def emoji_wordcloud(topic):
    src = emoji_wordcloud_urls[topic]
    return app.get_asset_url(src)

@app.callback(Output('wordcloud', 'src'),
              Input('source-dropdown', 'value'))
def wordcloud(topic):
    src = wordcloud_urls[topic]
    return app.get_asset_url(src)

# collapse components


def toggle_component(visibility):
    if visibility == 'on':
        return {'display': 'block'}
    if visibility == []:
        return {'display': 'none'}


@app.callback(
    Output("sentiment_bar_chart", "style"),
    [Input("sentiment_bar_chart_toggle", "value")],
)
def show_hide_element(visibility):
    return toggle_component(visibility)


@app.callback(
    Output("emoji-bar-chart", "style"),
    [Input("emoji-bar-chart-toggle", "value")],
)
def show_hide_element(visibility):
    return toggle_component(visibility)


@app.callback(
    Output("bar_chart_div", "style"),
    [Input("bar_chart_div-toggle", "value")],
)
def show_hide_element(visibility):
    return toggle_component(visibility)


@app.callback(
    Output("left-column", "style"),
    [Input("heatmap-container-toggle", "value")],
)
def show_hide_element(visibility):
    return toggle_component(visibility)


@app.callback(
    Output("news-hashtag-div", "style"),
    [Input("news-hashtag-div-toggle", "value")],
)
def show_hide_element(visibility):
    return toggle_component(visibility)


@app.callback(
    Output("daily-news", "style"),
    [Input("daily-news-toggle", "value")],
)
def show_hide_element(visibility):
    return toggle_component(visibility)


@app.callback(
    Output("hashtag-table", "style"),
    [Input("hashtag-table-toggle", "value")],
)
def show_hide_element(visibility):
    return toggle_component(visibility)


@app.callback(
    Output("covid-stats-container", "style"),
    [Input("deaths-and-cases-div-toggle", "value")],
)
def show_hide_element(visibility):
    return toggle_component(visibility)


@app.callback(
    Output("ma-sent-container", "style"),
    [Input("7-day-MA-div-toggle", "value")],
)
def show_hide_element(visibility):
    return toggle_component(visibility)


@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname == "/":
        return layout_faq
    elif pathname == "/page-1":
        return layout_main
    elif pathname == "/page-2":
        return layout_analysis
    # If the user tries to reach a different page, return a 404 message
    return dbc.Jumbotron(
        [
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"The pathname {pathname} was not recognised..."),
        ]
    )


if __name__ == '__main__':
    app.run_server(debug=True)
