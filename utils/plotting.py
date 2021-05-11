import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

import random
from dash.exceptions import PreventUpdate

pd.options.mode.chained_assignment = None  # Removes copy warning

case_str = 'newCasesByPublishDate'
death_str = 'newDeathsByDeathDate'
event_str = 'Event'
MA_win = 7


#     df_stats = df_stats.reindex(index=df_stats.index[::-1])  # Flipping df as dates are wrong way round (needed for MA)


def select_df_between_dates(df, start, end):
    date_list = [str(date.date())
                 for date in pd.date_range(start=start, end=end).tolist()]
    df = df.loc[df['date'].isin(date_list)]
    return df


def get_sent_vol_traces(df_sent, df_num_tweets, sentiment_type, events, country):
    sent_trace = get_sent_trace(df_sent, country, sentiment_type, events)
    vol_trace = get_vol_trace(df_num_tweets, country, events)
    return sent_trace, vol_trace


def get_sent_trace(df_sent, country, sentiment_type, events):
    sent_trace = go.Scatter(x=df_sent.loc[df_sent['region_name'] == country, 'date'],
                            y=df_sent.loc[df_sent['region_name']
                                          == country, sentiment_type],
                            name="{} 7 Day MA: Sentiment".format(country), text=events, textposition="bottom center"
                            )
    return sent_trace


def get_vol_trace(df_num_tweets, country, events):
    vol_trace = go.Scatter(x=df_num_tweets['date'], y=df_num_tweets[country],
                           name="{} 7 Day MA: Number of Tweets".format(country), text=events,
                           textposition="bottom center")
    return vol_trace


def get_stats_trace(data, events, country):
    case_trace = go.Scatter(x=data.loc[data['country'] == country, 'date'],
                            y=data.loc[data['country'] == country, case_str],
                            name="{} 7 Day MA: Covid Cases".format(country), text=events, textposition="bottom center")

    death_trace = go.Scatter(x=data.loc[data['country'] == country, 'date'],
                             y=data.loc[data['country'] == country, death_str],
                             name="{} 7 Day MA: Covid Deaths".format(country), text=events,
                             textposition="bottom center")
    return case_trace, death_trace


def plot_covid_stats(data, countries, events, start, end):
    df = select_df_between_dates(data, start, end)
    fig = make_subplots(rows=2, cols=2,
                        specs=[[{"secondary_y": True},
                                {"secondary_y": True}], [{"secondary_y": True},
                                                         {"secondary_y": True}]],
                        subplot_titles=('England', 'Scotland', 'NI', 'Wales'), vertical_spacing=0.25,
                        horizontal_spacing=0.3)
    for i, country in enumerate(countries):
        case_trace, death_trace = get_stats_trace(df, events, country)
        row, col = int((i / 2) + 1), (i % 2) + 1
        fig.add_trace(case_trace, secondary_y=False, row=row, col=col)
        fig.add_trace(death_trace, secondary_y=True, row=row, col=col)
    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.1,
        xanchor="right",
        x=1), height=750, autosize=True)
    fig.update_xaxes(title_text="Date", showgrid=False)
    fig.update_yaxes(title_text="Covid Cases",
                     secondary_y=False, showgrid=False)
    fig.update_yaxes(title_text="Covid Deaths",
                     secondary_y=True, showgrid=False)
    return fig


def plot_dropdown_sent_vs_vol(df_sent, df_vol, sentiment_col, events, countries, start, end):
    df_vol = select_df_between_dates(df_vol, start, end)
    df_sent = select_df_between_dates(df_sent, start, end)

    fig = make_subplots(rows=2, cols=2,
                        specs=[[{"secondary_y": True},
                                {"secondary_y": True}], [{"secondary_y": True},
                                                         {"secondary_y": True}]],
                        subplot_titles=('England', 'Scotland', 'NI', 'Wales'), vertical_spacing=0.25,
                        horizontal_spacing=0.2)
    for i, country in enumerate(countries):
        sent_trace, vol_trace = get_sent_vol_traces(
            df_sent, df_vol, sentiment_col, events, country)
        row, col = int((i / 2) + 1), (i % 2) + 1
        fig.add_trace(sent_trace, secondary_y=False, row=row, col=col)
        fig.add_trace(vol_trace, secondary_y=True, row=row, col=col)
        fig.update_yaxes(range=[-0.4, 0.5], row=row,
                         col=col, secondary_y=False)
    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.05,
        xanchor="right",
        x=1,
        itemsizing='constant'),
        height=750, autosize=True,
        margin=dict(l=20, r=20, t=80, b=20),
    )
    fig.update_xaxes(title_text="Date", showgrid=False)
    fig.update_yaxes(title_text="Sentiment(7MA)",
                     secondary_y=False, showgrid=False)
    fig.update_yaxes(title_text="Tweet Volume",
                     secondary_y=True, showgrid=False)

    return fig


def plot_hashtag_table(df):
    fig = go.Figure(data=[
        go.Table(
            header=dict(
                values=['<b>Hashtag<b>', '<b>Count<b>'],
                align='left',
                fill_color='paleturquoise',
            ),
            columnwidth=[300, 80],
            cells=dict(values=[df.Hashtag, df.Count], align='left', height=40)
        )
    ])
    fig.update_layout(autosize=True, height=500,
                      margin=dict(b=5, t=20, l=5, r=5))
    return fig


def plot_sentiment(df_sent, sentiment_column, start, end):
    df_sent = select_df_between_dates(df_sent, start, end)
    df_sent.rename(columns={'region_name': 'Country'}, inplace=True)
    fig = px.line(df_sent, x='date', y=sentiment_column, color='Country')

    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.05,
        xanchor="right",
        x=1,
        itemsizing='constant'),
        height=700, autosize=True,
        margin=dict(l=20, r=20, t=80, b=20),
    )
    range_list = [-0.4, 0.5] if sentiment_column != 'native-score_avg' else [-0.4, 0.6]
    fig.update_xaxes(title_text="Date", showgrid=False)
    fig.update_yaxes(title_text="Sentiment(7MA)",
                     secondary_y=False, showgrid=False, range=range_list)

    return fig


def plot_sentiment_comp(df_sent, start, end):
    df_sent = select_df_between_dates(df_sent, start, end)
    df_sent = df_sent.rename(columns={'nn-score_avg': 'lstm', 'textblob-score_avg': 'textblob',
                            'vader-score_avg': 'vader', 'native-score_avg': 'naive'})
    df = pd.melt(df_sent, id_vars=['date'],
                 value_vars=['lstm', 'textblob',
                             'vader', 'naive'],
                 var_name='sentiment_type',
                 value_name='sentiment_score'
                 )

    fig = px.line(df, x='date', y='sentiment_score', color='sentiment_type')

    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.05,
        xanchor="right",
        x=1,
        itemsizing='constant'),
        height=700, autosize=True,
        margin=dict(l=20, r=20, t=80, b=20),
    )
    fig.update_xaxes(title_text="Date", showgrid=False)
    fig.update_yaxes(title_text="Sentiment(7MA)",
                     secondary_y=False, showgrid=False, range=[-0.4, 0.5])

    return fig


def plot_sentiment_bar(df, sentiment_col, countries):
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
            df_sent = df_reg[df_reg[sentiment_col] == sentiment]
            sentiment_dict['count'].append(len(df_sent.index))
    fig = px.bar(pd.DataFrame(sentiment_dict), x='country',
                 y='count', color='sentiment', barmode='group')
    fig.update_layout(autosize=True)
    return fig


def plot_corr_mat(df, sentiment_col):
    df = df.rename(columns={sentiment_col: 'sentiment'})
    fig = px.scatter_matrix(df,
                            dimensions=['sentiment', 'volume', 'cases', 'deaths'],
                            color='country'
                            )
    fig.update_layout(autosize=True, height=500,
                      margin=dict(b=5, t=20, l=5, r=5))
    return fig


def plot_notable_days(df):
    fig = go.Figure(data=[
        go.Table(
            header=dict(
                values=['<b>Notable Label<b>',
                        '<b>Day/Month<b>', '<b>Ratio/Count<b>'],
                align='left',
                fill_color='paleturquoise',
            ),
            columnwidth=[120, 80, 80],
            cells=dict(values=['<b>' + df.notable_label + '<b>', df.date, df.rate],
                       fill=dict(color=['paleturquoise', 'white']),
                       align='left', height=60)
        )
    ])
    fig.update_layout(autosize=True, height=500,
                      margin=dict(b=5, t=20, l=5, r=5))
    return fig


def plot_sentiment_over_months(df):
    pass


def emoji_to_colour(emojis, r_min=0, r_max=255, g_min=0, g_max=255, b_min=0, b_max=255):
    mapping_colours = dict()

    for emoji in emojis.unique():
        red = random.randint(r_min, r_max)
        green = random.randint(g_min, g_max)
        blue = random.randint(b_min, b_max)
        rgb_string = 'rgb({}, {}, {})'.format(red, green, blue)

        mapping_colours[emoji] = rgb_string

    return mapping_colours


def plot_emoji_bar_chart(df, date):
    # mapping_colours = emoji_to_colour(df.emoji)
    # df['colour'] = df['emoji'].map(mapping_colours)
    if ((df['date'] == date).any()):
        fdata = df[df['date'] == date]
        title = 'Beginning: ' + date
        fig = go.Figure([go.Bar(x=fdata['emoji'], y=fdata['count'],
                                orientation='v',
                                marker_color=fdata['colour'], hoverinfo='none',
                                textposition='outside', texttemplate='%{x}<br>%{y}',
                                cliponaxis=False)],
                        layout=go.Layout(font={'size': 14},
                                         plot_bgcolor='#FFFFFF',
                                         xaxis={'showline': False,
                                                'visible': False},
                                         yaxis={'showline': False,
                                                'visible': False},
                                         bargap=0.1,
                                         title=title))
        fig.update_layout(
            margin=dict(
                l=10,
                r=10,
                b=50,
                t=100,
                pad=4
            ),
            barmode='stack',
            xaxis={'categoryorder': 'total descending'})
        return fig
    else:
        raise PreventUpdate


def frame_args(duration):
    return {
        "frame": {"duration": duration},
        "mode": "immediate",
        "fromcurrent": True,
        "transition": {"duration": duration, "easing": "linear"},
    }
