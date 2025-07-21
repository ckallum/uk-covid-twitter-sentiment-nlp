import json
import numpy as np
from .shared import load_data, get_data_sources, SENTIMENT_DROPDOWN_VALUE_TO_PREDICTIONS
from utils.plotting import plot_sentiment_bar

def fig_to_json(fig):
    """Convert a plotly figure to a JSON representation for the API"""
    fig_dict = fig.to_dict()
    
    class NumpyEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, np.integer):
                return int(obj)
            if isinstance(obj, np.floating):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            return super(NumpyEncoder, self).default(obj)
    
    sanitized_dict = json.loads(json.dumps(fig_dict, cls=NumpyEncoder))
    
    return {
        'data': sanitized_dict['data'],
        'layout': sanitized_dict['layout']
    }

def handler(request):
    """Get sentiment bar chart data"""
    try:
        date = request.args.get('date')
        source = request.args.get('source', 'covid')
        nlp_type = request.args.get('nlp_type', 'nn')
        
        if not date:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Date parameter is required'})
            }
        
        data_sources = get_data_sources()
        geo_df = data_sources['geo_df_data_sources'][source]
        predictions = SENTIMENT_DROPDOWN_VALUE_TO_PREDICTIONS[nlp_type]
        
        fig = plot_sentiment_bar(geo_df, date, predictions)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(fig_to_json(fig))
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        } 