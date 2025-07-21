import json
import numpy as np
from .shared import get_data_sources
from utils.plotting import plot_notable_days

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
    """Get notable days chart data"""
    try:
        topic = request.args.get('topic', 'covid')
        nlp_type = request.args.get('nlp_type', 'nn')
        
        data_sources = get_data_sources()
        notable_days_df = data_sources['notable_days_sources'][topic]
        
        fig = plot_notable_days(notable_days_df, nlp_type)
        
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