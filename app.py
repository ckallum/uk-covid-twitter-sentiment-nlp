import dash
import re
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
import json
from dash.dependencies import Input, Output
from utils.plotting import create_event_array, plot_covid_stats, format_df_ma_stats, format_df_ma_sent, \
    format_df_ma_tweet_vol, plot_sentiment_vs_volume
from utils.aggregations import aggregate_sentiment_by_region_type_by_date
from plotly.subplots import make_subplots

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.title = 'Sentiment Towards COVID-19 in the UK'

# READ DATA
df_covid_stats = pd.read_csv('data/COVID-Dataset/uk_covid_stats.csv', skipinitialspace=True)
uk_counties = json.load(open('data/Geojson/uk_counties_simpler.json', 'r'))
r_numbers = pd.read_csv('data/COVID-Dataset/r_numbers.csv')
df_events = pd.read_csv('data/events/key_events.csv', skipinitialspace=True, usecols=['Date', 'Event'])
countries = ['England', 'Scotland', 'Northern Ireland', 'Wales']
counties = pd.read_csv('data/Geojson/uk-district-list-all.csv')['county'].tolist()

# Data Sources
hashtag_data_sources = {'covid': pd.read_csv('data/covid/top_ten_hashtags_per_day.csv'),
                        'lockdown': pd.read_csv('data/lockdown/top_ten_hashtags_per_day.csv')}
geo_df_data_sources = {'covid': pd.read_csv('data/covid/daily_sentiment_county_updated_locations.csv'),
                          'lockdown': pd.read_csv('data/lockdown/daily_sentiment_county_updated_locations.csv')}

all_sentiment_data_sources = {'covid': pd.read_csv('data/covid/all_tweet_sentiments.csv'),
                              'lockdown': pd.read_csv('data/lockdown/all_tweet_sentiments.csv')}
sentiment_dropdown_value_to_score = {'nn': 'nn-predictions_avg_score', 'textblob': 'textblob-predictions_avg_score',
                                     'vader': 'vader-predictions_avg_score'}
sentiment_dropdown_value_to_labels = {'nn': 'nn-predictions', 'textblob': 'textblob-predictions',
                                      'vader': 'vader-predictions'}
tweet_counts_sources = {'covid': pd.read_csv('data/covid/daily_tweet_count_country.csv'),
                        'lockdown': pd.read_csv('data/lockdown/daily_tweet_count_country.csv')}
regions_lists = {'county': counties, 'country': countries}

# Dates
weeks = r_numbers['date'].tolist()
week_pairs = [(weeks[i], weeks[i + 1]) for i in range(0, len(weeks) - 1)]
start_global = '2020-03-20'
end_global = '2021-03-19'
dates_list = pd.date_range(start=start_global, end=end_global).tolist()

#
events_array = create_event_array(df_events, start_global, end_global)

# Initial map
covid_geo_df = geo_df_data_sources['covid'].loc[geo_df_data_sources['covid']['date'] == start_global]
fig_0 = px.choropleth_mapbox(
    covid_geo_df,
    locations="id",
    featureidkey='properties.id',
    geojson=uk_counties,
    color=sentiment_dropdown_value_to_score['nn'],
    hover_name='county',
    mapbox_style='white-bg',
    color_continuous_scale=px.colors.diverging.Temps_r,
    zoom=3.5,
    center={"lat": 55, "lon": 0},
    animation_frame='date',
    range_color=[-1, 1],
)


def df_to_table(df):
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in df.columns])] +

        # Body
        [
            html.Tr(
                [
                    html.Td(df.iloc[i][col])
                    for col in df.columns
                ]
            )
            for i in range(len(df))
        ]
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
            html.H6(
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
                html.P(id='region-selected', children='Select Region Grouping'),
                dcc.Dropdown(
                    id="region-dropdown",
                    options=[
                        {"label": "Counties", "value": "county"},
                        {"label": "Countries", "value": "country"}
                    ],
                    value="counties",
                    clearable=False,
                )],
                className="pretty_container three columns",
            ),
            html.Div(children=[
                html.P(id='data-selected', children='Select Tweet Data-set '),
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
            children=[
                # dcc.Interval(id='auto-stepper',
                #              interval=0,  # in milliseconds
                #              n_intervals=0),
                html.Div(children=[
                    filters(),
                    covid_stats_indicators()],
                    className='row'),
                html.Div(children=[
                    html.Button('Play', id='play-button', n_clicks=0)
                ]
                    , className='row'
                ),
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
                        className='pretty_container seven columns'
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
                        className='pretty_container five columns'
                    )

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
                    className='row'

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
                                        "label": "Moving Average",
                                        "value": "show_moving_average",
                                    },
                                    {
                                        "label": "Emoji Sentiment",
                                        "value": "show_emoji_sentiment",
                                    },
                                    {
                                        "label": "COVID Sentiment vs Time",
                                        "value": "show_sentiment_vs_time",
                                    },
                                    {
                                        'label': 'COVID'
                                    }
                                ],
                                value="show_death_rate_single_year",
                                id="chart-dropdown",
                            ),
                            dcc.Graph(
                                id='dropdown-figure'
                            ),
                        ],
                        className='pretty_container twelve columns'
                    ),
                    # html.Div(
                    #     [
                    #         html.P(
                    #             "Top 10 Hashtags",
                    #             style={
                    #                 "color": "#2a3f5f",
                    #                 "fontSize": "13px",
                    #                 "textAlign": "center",
                    #                 "marginBottom": "0",
                    #             },
                    #         ),
                    #         html.Div(
                    #             id="hashtags_table",
                    #             style={"padding": "10px 13px 5px 13px", "marginBottom": "5"},
                    #         ),
                    #     ],
                    #     className="pretty_container three columns",
                    #     style={
                    #         "backgroundColor": "white",
                    #         "border": "1px solid #C8D4E3",
                    #         "borderRadius": "10px",
                    #         "height": "100%"
                    #     },
                    # ),
                ],
                    className='row'
                )
            ],
        ),
    ],
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
    label = sentiment_dropdown_value_to_labels[nlp]
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


@app.callback(
    Output('hashtags_table', 'children'),
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
    return df_to_table(pd.DataFrame(hash_dict))


@app.callback(
    Output('days-slider', 'value'),
    [Input('auto-stepper', 'n_intervals')]
)
def play(n_clicks):
    if n_clicks is None:
        return 0
    else:
        return n_clicks + 1


@app.callback(
    Output("county-choropleth", "figure"),
    [Input("days-slider", "value"), Input("region-dropdown", "value"), Input("nlp-dropdown", "value"),
     Input("source-dropdown", "value")

     ]
)
def display_map(day, region, nlp, topic):
    geo_df = geo_df_data_sources[topic]
    color = sentiment_dropdown_value_to_score[nlp]
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
    return fig


@app.callback(
    Output("stats-graph", "figure"),
    [Input("days-slider", "value")
     ]
)
def display_stats(day):
    fig = make_subplots(rows=2, cols=2,
                        specs=[[{"secondary_y": True},
                                {"secondary_y": True}], [{"secondary_y": True},
                                                         {"secondary_y": True}]],
                        subplot_titles=('England', 'Scotland', 'NI', 'Wales'), vertical_spacing=0.3,
                        horizontal_spacing=0.2)
    df = format_df_ma_stats(df_covid_stats, countries, start_global, str(dates_list[day].date()))
    for i, country in enumerate(countries):
        case_trace, death_trace = plot_covid_stats(df, events_array, country)
        row, col = int((i / 2) + 1), (i % 2) + 1
        fig.add_trace(case_trace, secondary_y=False, row=row, col=col)
        fig.add_trace(death_trace, secondary_y=True, row=row, col=col)
    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1), height=600, width=1400)
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Covid Cases", secondary_y=False)
    fig.update_yaxes(title_text="Covid Deaths", secondary_y=True)
    return fig


@app.callback(
    Output('ma-sent-graph', 'figure'),
    [Input("days-slider", "value"), Input('source-dropdown', 'value'), Input('nlp-dropdown', 'value')]
)
def display_ma_sentiment(day, topic, sentiment_type):
    actual_date = str(dates_list[day].date())
    sentiment_col = sentiment_dropdown_value_to_score[sentiment_type]
    sentiment_data = all_sentiment_data_sources[topic]
    agg_data = aggregate_sentiment_by_region_type_by_date(sentiment_data, countries, 'country', start_global,
                                                          actual_date)
    df_sent, df_vol = format_df_ma_sent(agg_data, sentiment_dropdown_value_to_score[sentiment_type], start_global,
                                        actual_date), \
                      format_df_ma_tweet_vol(
                          tweet_counts_sources[topic],
                          countries,
                          start_global, actual_date)
    fig = make_subplots(rows=2, cols=2,
                        specs=[[{"secondary_y": True},
                                {"secondary_y": True}], [{"secondary_y": True},
                                                         {"secondary_y": True}]],
                        subplot_titles=('England', 'Scotland', 'NI', 'Wales'), vertical_spacing=0.3,
                        horizontal_spacing=0.2)
    for i, country in enumerate(countries):
        sent_trace, vol_trace = plot_sentiment_vs_volume(df_sent, df_vol, sentiment_col, events_array, country)
        row, col = int((i / 2) + 1), (i % 2) + 1
        fig.add_trace(sent_trace, secondary_y=False, row=row, col=col)
        fig.add_trace(vol_trace, secondary_y=True, row=row, col=col)
    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1), height=600, width=1400)
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Sentiment(7MA)", secondary_y=False)
    fig.update_yaxes(title_text="Tweet Volume", secondary_y=True)

    return fig


@app.callback(
    Output("daily-news", "children"),
    [Input("days-slider", "value")],
)
def display_news(day):
    date = str(dates_list[day].date())
    news_df = pd.read_csv('data/events/news_timeline.csv')
    news_df = news_df.loc[news_df['Date'] == date]
    # news_fig = ff.create_table(news_df.drop('Date', 1))
    # return df_to_table(news_df)
    links = ''
    for ind in news_df.index:
        headline = news_df['Headline'][ind]
        URL = news_df['URL'][ind]
        link = '[**' + headline + '**](' + URL + ') '
        blank = '''

        '''
        links = links + blank + link
    return (links)


if __name__ == '__main__':
    app.run_server(debug=True)

##TODO
