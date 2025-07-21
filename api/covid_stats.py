import json
from .shared import load_data

def handler(request):
    """Get COVID stats for a given date"""
    try:
        date = request.args.get('date')
        if not date:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Date parameter is required'})
            }
            
        data = load_data()
        df_covid_stats = data['df_covid_stats']
        
        total_deaths = df_covid_stats.loc[df_covid_stats['date'] == date, 'cumDeathsByDeathDate'].sum()
        total_cases = df_covid_stats.loc[df_covid_stats['date'] == date, 'cumCasesByPublishDate'].sum()
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'date': date,
                'total_deaths': int(total_deaths),
                'total_cases': int(total_cases)
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        } 