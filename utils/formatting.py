import json
from functools import reduce
import pandas as pd
from utils.aggregations import aggregate_sentiment_by_region_type_by_date
from utils.aggregations import aggregate_sentiment_per_day_per_country, aggregate_vol_per_day_per_country, \
    aggregate_stats_per_day_per_country, notable_month_by_sent_label, notable_months_count, notable_days_count, \
    notable_day_by_sent_label

start_global = '2020-03-20'
end_global = '2021-03-25'
dates_list = pd.date_range(start=start_global, end=end_global).tolist()
str_dates_list = [str(date.date()) for date in dates_list]

case_str = 'newCasesByPublishDate'
death_str = 'newDeathsByDeathDate'
event_str = 'Event'
MA_win = 7
countries = ['England', 'Scotland', 'Northern Ireland', 'Wales']
avg_cols = ['nn-score_avg', 'textblob-score_avg',
            'vader-score_avg', 'native-score_avg']

prediction_types = ['nn', 'vader', 'textblob', 'native']


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


def format_df_corr(df_sent, df_count, df_stats, sentiment_col, dates_list):
    countries = ['England', 'Scotland', 'Northern Ireland', 'Wales']
    sentiments_per_day_per_country = aggregate_sentiment_per_day_per_country(df_sent, dates_list, countries,
                                                                             sentiment_col)
    counts_per_day_per_country = aggregate_vol_per_day_per_country(df_count, dates_list, countries)
    deaths_per_day_per_country = aggregate_stats_per_day_per_country(df_stats, countries, death_str, dates_list)
    cases_per_day_per_country = aggregate_stats_per_day_per_country(df_stats, countries, case_str, dates_list)
    df_dict = dict(
        country=reduce(lambda x, y: x + y, [countries for _ in range(len(dates_list))]),
        sentiment=sentiments_per_day_per_country,
        volume=counts_per_day_per_country,
        cases=deaths_per_day_per_country,
        deaths=cases_per_day_per_country
    )
    return pd.DataFrame(df_dict)


def format_df_ma_stats(data, region_list):
    data = data.copy()
    for region in region_list:
        if len(data.index) < 7:
            data.loc[data['country'] == region, [death_str, case_str]] = data.loc[
                data['country'] == region, [death_str, case_str]].rolling(
                window=1).mean().dropna()  # 7 Day MA
        else:
            data.loc[data['country'] == region, [death_str, case_str]] = data.loc[
                data['country'] == region, [death_str, case_str]].rolling(
                window=MA_win).mean().dropna()
    return data


def format_df_ma_tweet_vol(data, region_list):
    new_data = data.copy()
    for region in region_list:
        if len(data.index) < 7:
            new_data.loc[:, region] = data.loc[:, region].rolling(window=len(data.index)).mean().dropna()
        else:
            new_data.loc[:, region] = data.loc[:, region].rolling(window=MA_win).mean().dropna()
    return new_data.dropna()


def format_df_ma_sent(df):
    df = aggregate_sentiment_by_region_type_by_date(df, countries, 'country', start_global,
                                                    end_global).copy()
    for region in df['region_name'].unique():
        if len(df.index) < 7:
            df.loc[df['region_name'] == region, avg_cols] = df.loc[df['region_name'] == region, avg_cols].rolling(
                window=len(df.index)).mean().dropna()  # 7 Day MA
        else:
            df.loc[df['region_name'] == region, avg_cols] = df.loc[df['region_name'] == region, avg_cols].rolling(
                window=MA_win).mean().dropna()  # 7 Day MA
    return df


def format_df_notable_days(df_sent, df_count):
    indexes = ['max_day', 'max_month', 'pos_day', 'pos_month', 'neg_day', 'neg_month']
    result_df_list = []
    for sentiment in prediction_types:
        columns = {'date': [], 'rate': [], 'sentiment_type': []}
        max_day, day_count = notable_days_count(df_count, str_dates_list, countries)
        max_month, month_count = notable_months_count(df_count, countries)
        pos_day, day_pos_rate = notable_day_by_sent_label(df_sent, sentiment, 'pos', str_dates_list)
        pos_month, month_pos_rate = notable_month_by_sent_label(df_sent, sentiment, 'pos')
        neg_day, day_neg_rate = notable_day_by_sent_label(df_sent, sentiment, 'neg', str_dates_list)
        neg_month, month_neg_rate = notable_month_by_sent_label(df_sent, sentiment, 'neg')

        columns['sentiment_type'].append(sentiment)
        columns['date'] += [max_day, max_month, pos_day, pos_month, neg_day, neg_month]
        columns['rate'] += [day_count, month_count, day_pos_rate, month_pos_rate, day_neg_rate, month_neg_rate]
        data = pd.DataFrame(columns, index=indexes)
        result_df_list.append(data)
    df = pd.concat(result_df_list, axis=0)

    return df

# def scale(df_sent, df_vol):
#     scaler = MinMaxScaler()
#     scaled_vol = scaler.fit_transform(df_vol.loc[:, countries])
#     new_df = []
#     for j, country in enumerate(countries):
#         region_df = df_sent.loc[df_sent['region_name'] == country]
#         for i, d in region_df.iterrows():
#             region_df.loc[i, ['nn-predictions_avg_score', 'textblob-predictions_avg_score',
#                               'vader-predictions_avg_score']] *= scaled_vol[i%4][j]
#         new_df.append(region_df)
#     new = pd.concat(new_df, axis=0)
#     return new
