import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

pd.options.mode.chained_assignment = None  # Removes copy warning

case_str = 'newCasesByPublishDate'
death_str = 'newDeathsByDeathDate'
event_str = 'Event'
MA_win = 7


#     df_stats = df_stats.reindex(index=df_stats.index[::-1])  # Flipping df as dates are wrong way round (needed for MA)

def create_event_array(df_events, start, end):
    date_list = [str(date.date().strftime('%d-%m-%Y')) for date in pd.date_range(start=start, end=end).tolist()]
    event_arr = []
    for date in date_list:
        if date in df_events['Date'].unique():
            event = df_events.loc[df_events['Date'] == date]['Event']
            event_arr.append(event.values[0])
        else:
            event_arr.append('')

    return event_arr


def select_df_between_dates(df, start, end):
    date_list = [str(date.date()) for date in pd.date_range(start=start, end=end).tolist()]
    df = df.loc[df['date'].isin(date_list)]
    return df


def format_df_ma_sent(data, sentiment_col, start, end):
    data = select_df_between_dates(data, start, end)
    region_df_sent_dict = {}
    for region in data['region_name'].unique():
        temp_sent = data.loc[data['region_name'] == region]  # Splitting DF into countries
        if len(temp_sent.index) < 7:
            temp_sent.loc[:, sentiment_col] = temp_sent.loc[:, sentiment_col].rolling(
                window=len(data.index)).mean().dropna()  # 7 Day MA
        else:
            temp_sent.loc[:, sentiment_col] = temp_sent.loc[:, sentiment_col].rolling(
                window=MA_win).mean().dropna()  # 7 Day MA
        region_df_sent_dict[region] = temp_sent.dropna()
    return region_df_sent_dict


def format_df_ma_stats(data, region_list, start, end):
    data = select_df_between_dates(data, start, end)
    region_df_stats_dict = {}
    for region in region_list:
        temp_stats = data.loc[data['country'] == region]
        if len(temp_stats.index) < 7:
            temp_stats.loc[:, [death_str, case_str]] = temp_stats.loc[:, [death_str, case_str]].rolling(
                window=len(data.index)).mean().dropna()  # 7 Day MA
        else:
            temp_stats.loc[:, [death_str, case_str]] = temp_stats.loc[:, [death_str, case_str]].rolling(
                window=MA_win).mean().dropna()
        region_df_stats_dict[region] = temp_stats.dropna()
    return region_df_stats_dict


def format_df_ma_tweet_vol(df, region_list, start, end):
    data = select_df_between_dates(df, start, end)
    for region in region_list:
        if len(data.index) < 7:
            data.loc[:, region] = data.loc[:, region].rolling(window=len(data.index)).mean().dropna()
        else:
            data.loc[:, region] = data.loc[:, region].rolling(window=MA_win).mean().dropna()
    return data


def get_sent_vol_traces(df_sent, df_num_tweets, sentiment_type, events, country):
    sent_trace = go.Scatter(x=df_sent[country]['date'], y=df_sent[country][sentiment_type],
                            name="{} 7 Day MA: Sentiment".format(country), text=events, textposition="bottom center"
                            )

    vol_trace = go.Scatter(x=df_num_tweets['date'], y=df_num_tweets[country],
                           name="{} 7 Day MA: Number of Tweets".format(country), text=events,
                           textposition="bottom center")
    return sent_trace, vol_trace


def plot_sentiment_vs_volume(agg_data, tweet_count_data, sentiment_col, events, countries, start, end):
    df_sent, df_vol = format_df_ma_sent(agg_data, sentiment_col, start,
                                        end), \
                      format_df_ma_tweet_vol(
                          tweet_count_data,
                          countries,
                          start, end)
    fig = make_subplots(rows=2, cols=2,
                        specs=[[{"secondary_y": True},
                                {"secondary_y": True}], [{"secondary_y": True},
                                                         {"secondary_y": True}]],
                        subplot_titles=('England', 'Scotland', 'NI', 'Wales'), vertical_spacing=0.25,
                        horizontal_spacing=0.3)
    for i, country in enumerate(countries):
        sent_trace, vol_trace = get_sent_vol_traces(df_sent, df_vol, sentiment_col, events, country)
        row, col = int((i / 2) + 1), (i % 2) + 1
        fig.add_trace(sent_trace, secondary_y=False, row=row, col=col)
        fig.add_trace(vol_trace, secondary_y=True, row=row, col=col)
        fig.update_yaxes(range=[-0.4, 0.4], row=row, col=col, secondary_y=False)
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
    fig.update_yaxes(title_text="Sentiment(7MA)", secondary_y=False, showgrid=False)
    fig.update_yaxes(title_text="Tweet Volume", secondary_y=True, showgrid=False)

    return fig


def get_stats_trace(data, events, country):
    case_trace = go.Scatter(x=data[country]['date'], y=data[country][case_str],
                            name="{} 7 Day MA: Covid Cases".format(country), text=events, textposition="bottom center")

    death_trace = go.Scatter(x=data[country]['date'], y=data[country][death_str],
                             name="{} 7 Day MA: Covid Deaths".format(country), text=events,
                             textposition="bottom center")
    return case_trace, death_trace


def plot_covid_stats(data, countries, events, start, end):
    df = format_df_ma_stats(data, countries, start, end)
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
        y=1.05,
        xanchor="right",
        x=0.88), height=750, autosize=True)
    fig.update_xaxes(title_text="Date", showgrid=False)
    fig.update_yaxes(title_text="Covid Cases", secondary_y=False, showgrid=False)
    fig.update_yaxes(title_text="Covid Deaths", secondary_y=True, showgrid=False)
    return fig


def plot_hashtag_table(df):
    fig = go.Figure(data=[
        go.Table(
            header=dict(
                values=['Hashtag', 'Count'],
                align='left',
                fill_color='paleturquoise',
            ),
            columnwidth=[300, 80],
            cells=dict(values=[df.Hashtag, df.Count], align='left',height=40)
        )
    ])
    fig.update_layout(autosize=True, height=500, margin=dict(b=5, t=20))
    return fig
