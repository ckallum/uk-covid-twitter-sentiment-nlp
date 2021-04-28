import pandas as pd

avg_score_columns = ['nn-score_avg', 'textblob-score_avg',
                     'vader-score_avg', 'native-score_avg']
score_columns = {'nn': 'nn-score', 'textblob': 'textblob-score',
                 'vader': 'vader-score', 'native': 'native-score'}
prediction_columns = {'nn': 'nn-predictions', 'vader': 'vader-predictions', 'textblob': 'textblob-predictions',
                      'native': 'native-predictions'}
prediction_types = ['nn', 'vader', 'textblob', 'native']
sentiments = {'neg': -1, 'pos': 1, 'neu': 0}

number_to_month = {
    '2021-01': 'January 2021',
    '2021-02': 'February 2021',
    '2021-03': 'March 2021',
    '2020-03': 'March 2020',
    '2020-04': 'April 2020',
    '2020-05': 'May 2020',
    '2020-06': 'June 2020',
    '2020-07': 'July 2020',
    '2020-08': 'August 2020',
    '2020-09': 'September 2020',
    '2020-10': 'October 2020',
    '2020-11': 'November 2020',
    '2020-12': 'December 2020',
}

months = ['January 2021',
          'February 2021',
          'March 2021',
          'March 2020',
          'April 2020',
          'May 2020',
          'June 2020',
          'July 2020',
          'August 2020',
          'September 2020',
          'October 2020',
          'November 2020',
          'December 2020']


def map_dates_to_months(df):
    map_func = lambda x: number_to_month[x[:7]]
    new_df = df.copy()
    new_df['date'] = df['date'].map(map_func)
    return new_df


def map_label_to_score(df, label):
    map_func = lambda x: sentiments[x]
    df[label] = df[label].map(map_func)
    return df



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
                       prediction_version in prediction_types}
    dates = []
    regions = []
    data['date'] = pd.to_datetime(data.date)
    for date in date_list:
        date_data = data.loc[data['date'] == date]
        for region in region_list:
            region_data = date_data.loc[date_data[region_header] == region]
            dates.append(date)
            regions.append(region)
            for i, prediction_version in enumerate(avg_score_columns):
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

def notable_day_by_sent_label(df, column, label, dates):
    resulting_day, result_ratio = None, 0
    column = prediction_columns[column]
    for day in dates:
        daily_df = df.loc[df['date'] == day]
        label_ratio = len(daily_df.loc[daily_df[column] == label].index) / len(daily_df.index)
        if label_ratio > result_ratio:
            result_ratio = label_ratio
            resulting_day = day
    return resulting_day, result_ratio


def notable_month_by_sent_label(df, column, label):

    df = map_dates_to_months(df)

    resulting_month, result_ratio = None, 0
    column = prediction_columns[column]
    for month in months:
        monthly_df = df.loc[df['date'] == month]
        label_ratio = len(monthly_df.loc[monthly_df[column] == label].index) / len(monthly_df.index)
        if label_ratio > result_ratio:
            result_ratio = label_ratio
            resulting_month = month
    return resulting_month, result_ratio


def notable_days_count(df, dates, countries):
    highest_vol, highest_day = 0, None
    for day in dates:
        daily_df = df.loc[df['date'] == day]
        total_vol = daily_df.loc[:, countries].sum(axis=1).values[0]
        if total_vol > highest_vol:
            highest_vol = total_vol
            highest_day = day
    return highest_day, highest_vol


def notable_months_count(df, countries):
    df = map_dates_to_months(df)
    highest_vol, highest_month = 0, None
    for month in months:
        monthly_df = df.loc[df['date'] == month]
        total_vol = monthly_df.loc[:, countries].sum(axis=1).values[0]
        if total_vol > highest_vol:
            highest_vol = total_vol
            highest_month = month
    return highest_month, highest_vol


def aggregate_all_cases_over_time(data):
    pass

