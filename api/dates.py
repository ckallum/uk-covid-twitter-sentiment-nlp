import json
import pandas as pd
from .shared import load_data

def handler(request):
    """Return all dates in the dataset"""
    try:
        data = load_data()
        
        # Dates
        start_global = '2020-03-20'
        end_global = '2021-03-25'
        dates_list = pd.date_range(start=start_global, end=end_global)
        str_dates_list = [str(date.date()) for date in dates_list]
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'dates': str_dates_list,
                'start_date': start_global,
                'end_date': end_global
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        } 