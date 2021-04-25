import pandas as pd

score_columns = ['nn-predictions_avg_score', 'vader-predictions_avg_score', 'textblob-predictions_avg_score']
prediction_columns = ['nn-predictions', 'vader-predictions', 'textblob-predictions']
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
    score_by_region = {'{}_avg_score'.format(prediction_version): [] for
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


def aggregate_all_cases_over_time(data):
    pass