import pandas as pd

score_columns = ['nn-score_avg', 'textblob-score_avg',
                 'vader-score_avg', 'native-score_avg']
prediction_columns = ['nn', 'vader', 'textblob', 'native']
sentiments = {'neg': -1, 'pos': 1, 'neu': 0}


def aggregate_sentiment_by_region_type_by_date(data, region_list, region_header,
                                               start,
                                               end):
    """
    :param data:
    :param region_list:
    :param region_header:
    :param start:
    :param end:
    :return:
    DataFrame where each column is each region, each row is each date. Cells contain average sentiment/score of that region
    within specified date.

    """
    date_list = [str(date.date()) for date in pd.date_range(start=start, end=end).tolist()]
    score_by_region = {'{}-score_avg'.format(prediction_version): [] for
                       prediction_version in prediction_columns}
    dates = []
    regions = []
    data['date'] = pd.to_datetime(data.date)
    for date in date_list:
        date_data = data.loc[data['date'] == date]
        for region in region_list:
            region_data = date_data.loc[date_data[region_header] == region]
            dates.append(date)
            regions.append(region)
            for i, prediction_version in enumerate(score_columns):
                if not region_data.empty:
                    score_by_region[prediction_version].append(
                        region_data[prediction_version].mean())
    full_data = pd.concat(
        [pd.DataFrame({'date': dates}), pd.DataFrame({'region_name': regions}),
         pd.DataFrame(score_by_region)], axis=1)
    return full_data


def aggregate_sentiment_per_day_per_country(df_sent, dates, countries, sentiment_col):
    sentiments = []
    for date in dates:
        date_df = df_sent.loc[df_sent['date'] == date]
        for country in countries:
            region_df = date_df.loc[date_df['country'] == country]
            sentiments.append(region_df[sentiment_col].mean())
    return sentiments


def aggregate_vol_per_day_per_country(df_count, dates, countries):
    volume_list = []
    for date in dates:
        for country in countries:
            if date not in df_count['date'].tolist():
                volume_list.append(0)
            else:
                volume_list.append(df_count.loc[df_count['date'] == date, country].values[0])
    return volume_list


def aggregate_stats_per_day_per_country(df_stats, countries, col, dates):
    stats_list = []
    for date in dates:
        df_stats['date'] = pd.to_datetime(df_stats.date, format='%Y-%m-%d')
        dates_df = df_stats.loc[df_stats['date'] == date]
        for country in countries:
            stats_list.append(dates_df.loc[dates_df['country'] == country, col].values[0])
    return stats_list


def aggregate_all_cases_over_time(data):
    pass
