import pandas as pd
import plotly.graph_objects as go

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
                window=len(temp_sent.index)).mean().dropna()  # 7 Day MA
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
                window=len(temp_stats.index)).mean().dropna()  # 7 Day MA
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


def plot_sentiment_vs_volume(df_sent, df_num_tweets, sentiment_type, events, country):
    sent_trace = go.Scatter(x=df_sent[country]['date'], y=df_sent[country][sentiment_type],
                            name="{} 7 Day MA: Sentiment".format(country), text=events, textposition="bottom center")

    vol_trace = go.Scatter(x=df_num_tweets['date'], y=df_num_tweets[country],
                           name="{} 7 Day MA: Number of Tweets".format(country), text=events,
                           textposition="bottom center")
    return sent_trace, vol_trace


def plot_covid_stats(data, events, country):
    case_trace = go.Scatter(x=data[country]['date'], y=data[country][case_str],
                            name="{} 7 Day MA: Covid Cases".format(country), text=events, textposition="bottom center")

    death_trace = go.Scatter(x=data[country]['date'], y=data[country][death_str],
                             name="{} 7 Day MA: Covid Deaths".format(country), text=events,
                             textposition="bottom center")
    return case_trace, death_trace

# def plot(topic, sentiment_type, region_type, country, start, end):
#     df_sent, df_stats, df_num_tweet = select_df_between_dates(start, end, df_sent, df_stats, df_num_tweet)
#
#     sentiment_avg_col = sentiment_type + '_avg_score'
#
#     region_df_sent_dict, region_df_stats_dict = split_df(df_sent, df_stats, region_type,
#                                                          df_num_tweet, sentiment_avg_col)
#     # print(region_df_sent_dict)
#     event_arr = create_event_array(df_events, start, end, event_str)
#     fig = make_subplots(rows=2, cols=1, specs=[[{"secondary_y": True}], [{"secondary_y": True}]],
#                         subplot_titles=("Number of tweets and sentiment", "Spread of the virus"))
#     fig.add_trace(
#         go.Scatter(x=region_df_sent_dict[country]['date'], y=region_df_sent_dict[country][sentiment_avg_col],
#                    name="7 Day MA: Sentiment", text=event_arr, textposition="bottom center"), secondary_y=False,
#         row=1, col=1, )
#     fig.add_trace(
#         go.Scatter(x=df_num_tweet['date'], y=df_num_tweet[country],
#                    name="7 Day MA: Number of Tweets", text=event_arr, textposition="bottom center"), secondary_y=True,
#         row=1, col=1, )
#     fig.add_trace(
#         go.Scatter(x=region_df_stats_dict[country]['date'], y=region_df_stats_dict[country][case_str],
#                    name="7 Day MA: Covid Cases", text=event_arr, textposition="bottom center"), secondary_y=False,
#         row=2, col=1, )
#     fig.add_trace(
#         go.Scatter(x=region_df_stats_dict[country]['date'], y=region_df_stats_dict[country][death_str],
#                    name="7 Day MA: Covid Deaths", text=event_arr, textposition="bottom center"), secondary_y=True,
#         row=2, col=1, )
#
#     fig.update_layout(title_text=country)
#     fig.update_xaxes(title_text="Date")
#     fig.update_yaxes(title_text="Sentiment", secondary_y=False, row=1, col=1)
#     fig.update_yaxes(title_text="Number of Tweets", secondary_y=True, row=1, col=1)
#     fig.update_yaxes(title_text="Covid Cases", secondary_y=False, row=2, col=1)
#     fig.update_yaxes(title_text="Covid Deaths", secondary_y=True, row=2, col=1)
#     return fig

# plot('covid', 'nn-predictions', 'country', 'England', '2020-03-20', '2021-03-25').show()
