import dash
import re
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
import json
from dash.dependencies import Input, Output, State
from utils.formatting import create_event_array
from utils.plotting import plot_animated_sent, plot_covid_stats, plot_hashtag_table, \
    plot_sentiment_vs_volume, plot_corr_mat
from utils.aggregations import aggregate_sentiment_by_region_type_by_date, aggregate_all_cases_over_time
from plotly.subplots import make_subplots
from utils.formatting import format_df_ma_stats, format_df_ma_sent, format_df_ma_tweet_vol, format_df_corr

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets
                )

server = app.server
app.title = 'Sentiment Towards COVID-19 in the UK'

# READ DATA
df_covid_stats = pd.read_csv('data/COVID-Dataset/uk_covid_stats.csv', skipinitialspace=True)
uk_counties = json.load(open('data/Geojson/uk_counties_simpler.json', 'r'))
r_numbers = pd.read_csv('data/COVID-Dataset/r_numbers.csv')
df_events = pd.read_csv('data/events/key_events.csv', skipinitialspace=True, usecols=['Date', 'Event'])
counties = pd.read_csv('data/Geojson/uk-district-list-all.csv')['county'].tolist()
all_covid = pd.read_csv('data/covid/all_tweet_sentiments.csv')
all_lockdown = pd.read_csv('data/lockdown/all_tweet_sentiments.csv')
hashtags_covid = pd.read_csv('data/covid/top_ten_hashtags_per_day.csv')
hashtags_lockdown = pd.read_csv('data/lockdown/top_ten_hashtags_per_day.csv')
geo_df_covid = pd.read_csv('data/covid/daily_sentiment_county_updated_locations.csv')
geo_df_lockdown = pd.read_csv('data/lockdown/daily_sentiment_county_updated_locations.csv')
tweet_count_covid = pd.read_csv('data/covid/daily_tweet_count_country.csv')
tweet_count_lockdown = pd.read_csv('data/lockdown/daily_tweet_count_country.csv')
news_df = pd.read_csv('data/events/news_timeline.csv')

countries = ['England', 'Scotland', 'Northern Ireland', 'Wales']

# Data Sources
hashtag_data_sources = {'covid': hashtags_covid,
                        'lockdown': hashtags_lockdown}
geo_df_data_sources = {'covid': geo_df_covid,
                       'lockdown': geo_df_lockdown}

all_sentiment_data_sources = {'covid': all_covid,
                              'lockdown': all_lockdown}
sentiment_dropdown_value_to_avg_score = {'nn': 'nn-predictions_avg_score', 'textblob': 'textblob-predictions_avg_score',
                                         'vader': 'vader-predictions_avg_score'}
sentiment_dropdown_value_to_score = {'nn': 'nn-score', 'textblob': 'textblob-score',
                                     'vader': 'vader-score'}
sentiment_dropdown_value_to_predictions = {'nn': 'nn-predictions', 'textblob': 'textblob-predictions',
                                           'vader': 'vader-predictions'}
tweet_counts_sources = {'covid': tweet_count_covid,
                        'lockdown': tweet_count_lockdown}
regions_lists = {'county': counties, 'country': countries}

# Formatted
formatted_tweet_count = {'covid': format_df_ma_tweet_vol(tweet_count_covid, countries),
                         'lockdown': format_df_ma_tweet_vol(tweet_count_lockdown, countries)}
formatted_tweet_sent = {'covid': format_df_ma_sent(geo_df_covid), 'lockdown': format_df_ma_sent(geo_df_lockdown)}

formatted_covid_stats = format_df_ma_stats(df_covid_stats, countries)

# Dates
weeks = r_numbers['date'].tolist()
week_pairs = [(weeks[i], weeks[i + 1]) for i in range(0, len(weeks) - 1)]
start_global = '2020-03-20'
end_global = '2021-03-25'
dates_list = pd.date_range(start=start_global, end=end_global)

#
events_array = create_event_array(df_events, start_global, end_global)

# Initial map
covid_geo_df = geo_df_data_sources['covid'].loc[geo_df_data_sources['covid']['date'] == start_global]
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
                        {"label": "NN", "value": "nn"}
                    ],
                    value="nn",
                    clearable=False,
                )],
                className="pretty_container three columns",
            )
        ],
        className="eight columns",
        style={"margin-bottom": "10px"},
    )


#  App Layout
app.layout = html.Div(
    id="root",
    children=[
        html.Div(
            id="header",
            children=[
                html.H4(
                    children="Sentiment of Tweets about COVID-19 in the UK by County"),
            ],
        ),

        html.Div(
            id="app-container",
            children=[dcc.Interval(
                id="interval-component",
                interval=2 * 1000,  # in milliseconds
                n_intervals=0,  # start at batch 50
                disabled=True,
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
                                    html.H6(
                                        "Tweet Sentiment Ratio Within Each Country",
                                        id="barchart-title",
                                    ),
                                    dcc.Graph(
                                        id='sentiment_bar_chart'
                                    ),
                                ],
                            ),
                        ],
                        className='pretty_container four columns'
                    ),
                    html.Div(
                        [
                            html.P(
                                "Top 10 Hashtags",
                                style={
                                    "color": "#2a3f5f",
                                    "fontSize": "13px",
                                    "textAlign": "center",
                                    "marginBottom": "0",
                                },
                            ),
                            dcc.Graph(
                                id='hashtag-table'
                            )
                        ],
                        className="pretty_container three columns",
                    ),

                ],
                    className='row'
                )
                ,
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
                                    "7 Day MA Sentiment vs Tweet Volume",
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
                html.Div(

                    children=[
                        html.H6(
                            "Top News Stories",
                        ),
                        dcc.Markdown(
                            id="daily-news",
                            style={"padding": "10px 13px 5px 13px", "marginBottom": "5"},
                        )
                    ],
                    className='pretty_container three columns'
                ),
                html.Div(children=[
                    html.Div(
                        id="graph-container",
                        children=[
                            html.P(id="chart-selector", children="Select Animated Charts:"),
                            dcc.Dropdown(
                                options=[
                                    {
                                        "label": "Emoji Sentiment",
                                        "value": "show_emoji_sentiment",
                                    },
                                    {
                                        "label": "COVID Sentiment vs Time",
                                        "value": "show_sentiment_vs_time",
                                    },
                                    {
                                        "label": "Popular Hashtags vs Time",
                                        "value": "show_hashtags_vs_time",
                                    },
                                    {
                                        "label": "Hashtags vs Sentiment",
                                        "value": "show_hashtags_vs_sentiment",
                                    },
                                    {
                                        "label": "Sentiment vs Cases",
                                        "value": "show_cases_vs_sentiment",
                                    },
                                ],
                                value="show_sentiment_vs_time",
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
                html.Div(
                    children=[
                        html.Div(
                            children=[
                                html.H4(
                                    children='Sentiment vs Tweet Volume'
                                ),
                            ],
                            className='pretty_container six columns'
                        ),
                        html.Div(
                            children=[
                                html.H4(
                                    children=[
                                        'Correlation Between Features',
                                        dcc.Graph(
                                            id='corr-mat'
                                        ),
                                    ]
                                ),
                            ],
                            className='pretty_container six columns'
                        )
                    ],
                    className='row'
                )
            ]
        )
    ]
)


@app.callback(Output('r_number_indicator', 'children'), [Input("days-slider", "value")])
def update_r_text(date_index):
    selected_date = str(dates_list[date_index].date())
    for i, (start, end) in enumerate(week_pairs):
        if check_between_dates(start, end, selected_date):
            df = r_numbers.loc[r_numbers['date'] == start]
            avg_r = round(float((df['upper'] + df['lower']) / 2), 2)
            if avg_r == 0:
                return 'N/A'
            return "~{}".format(avg_r)
    return 'N/A'


@app.callback(Output('total_cases_indicator', 'children'), [Input("days-slider", "value")])
def update_cases_text(date_index):
    selected_date = str(dates_list[date_index].date())
    cases = df_covid_stats.loc[df_covid_stats['date'] == selected_date, 'cumCasesByPublishDate'].sum()
    return cases


@app.callback(Output('total_deaths_indicator', 'children'), [Input("days-slider", "value")])
def update_deaths_text(date_index):
    selected_date = str(dates_list[date_index].date())
    deaths = df_covid_stats.loc[df_covid_stats['date'] == selected_date, 'cumDeathsByDeathDate'].sum()
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
    [Input("days-slider", "value"), Input('source-dropdown', 'value'), Input('nlp-dropdown', 'value')]
)
def update_bar_chart(selected_date, source, nlp):
    data = all_sentiment_data_sources[source]
    data['date'] = pd.to_datetime(data['date']).dt.date
    df = data[data['date'] == dates_list[selected_date]]
    label = sentiment_dropdown_value_to_predictions[nlp]
    countries = ['England', 'Scotland', 'Northern Ireland', 'Wales']
    sentiment_labels = ['neg', 'neu', 'pos']
    sentiment_dict = {
        'country': [],
        'count': [],
        'sentiment': []
    }
    for sentiment in sentiment_labels:
        for country in countries:
            sentiment_dict['country'].append(country)
            sentiment_dict['sentiment'].append(sentiment)
            df_reg = df[df['country'] == country]
            df_sent = df_reg[df_reg[label] == sentiment]
            sentiment_dict['count'].append(len(df_sent.index))
    fig = px.bar(pd.DataFrame(sentiment_dict), x='country', y='count', color='sentiment', barmode='group')
    return fig


#
@app.callback(
    Output('hashtag-table', 'figure'),
    [Input("days-slider", "value"), Input('source-dropdown', 'value')]
)
def update_hashtag_table(selected_date, source):
    selected_date = str(dates_list[selected_date].date())
    hashtags_df = hashtag_data_sources[source]
    hashtag_date = hashtags_df.loc[hashtags_df['date'] == selected_date]
    hashtags = [tuple(x.split(',')) for x in re.findall("\((.*?)\)", hashtag_date['top_ten_hashtags'].values[0])]
    hash_dict = {'Hashtag': [], 'Count': []}
    for hashtag, count in hashtags:
        hash_dict['Hashtag'].append('#' + hashtag.replace("'", ''))
        hash_dict['Count'].append(count)
    hash_df = pd.DataFrame(hash_dict)
    return plot_hashtag_table(hash_df)

# @app.callback(
#     [Output('days-slider', 'value'), Output('interval-component', 'disabled'), Output('play-button', 'children')],
#     [Input('next-button', 'n_clicks'), Input('prev-button', 'n_clicks'), Input('next-button', 'n_clicks'),
#      Input('interval-component', 'n_intervals')],
#     [State('days-slider', 'value'), State('play-button', 'children')]
# )
# def button_pressed(inc_btn, dec_btn, play_btn, interval, day, play_txt):
#     changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
#     if 'next-button' in changed_id:
#         if day < 364:
#             return day + 1, False, play_txt
#     if 'prev-button' in changed_id:
#         if day > 0:
#             return day - 1, False, play_txt
#     if 'play-button' in changed_id:
#         return day + 1, False, play_txt
#     return day
#

@app.callback(
    Output('days-slider', 'value'),
    [Input('next-button', 'n_clicks'), Input('prev-button', 'n_clicks'), State('days-slider', 'value')]
)
def button_pressed(inc_btn, dec_btn, day):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if 'next-button' in changed_id:
        if day < 364:
            return day + 1
    if 'prev-button' in changed_id:
        if day > 0:
            return day - 1
    return day


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
    fig.update_layout(autosize=True)
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
    [Input("days-slider", "value"), Input('source-dropdown', 'value'), Input('nlp-dropdown', 'value')]
)
def display_sentiment_vs_vol(day, topic, sentiment_type):
    selected_date = str(dates_list[day].date())
    sentiment_col = sentiment_dropdown_value_to_avg_score[sentiment_type]
    tweet_count_df = formatted_tweet_count[topic]
    tweet_sent_df = formatted_tweet_sent[topic]
    return plot_sentiment_vs_volume(tweet_sent_df, tweet_count_df, sentiment_col, events_array, countries, start_global,
                                    selected_date)


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
    [Input('source-dropdown', 'value'), Input('nlp-dropdown', 'value'), Input('chart-dropdown', 'value')]
)
def animated_chart(topic, sentiment_type, chart_value):
    sentiment_col = sentiment_dropdown_value_to_avg_score[sentiment_type]
    # "value": "show_emoji_sentiment"
    # "value": "show_hashtags_vs_time"
    # "value": "show_hashtags_vs_sentiment"

    # "value": "show_cases_vs_sentiment"
    if chart_value == 'show_sentiment_vs_time':
        return plot_animated_sent(formatted_tweet_sent[topic], formatted_tweet_count[topic], sentiment_col,
                                  events_array, dates_list)
    return None


@app.callback(
    Output('corr-mat', 'figure'),
    [Input('root', 'children')],
    [State('source-dropdown', 'value'), State('nlp-dropdown', 'value')]
)
def correlation_matrix(root, topic, sentiment_type):
    df_sent = geo_df_data_sources[topic]
    vol_df = tweet_counts_sources[topic]
    sentiment_col = sentiment_dropdown_value_to_avg_score[sentiment_type]
    data = format_df_corr(df_sent, vol_df, df_covid_stats, sentiment_col, [str(date.date()) for date in dates_list])
    fig = plot_corr_mat(data)
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)

##TODO
