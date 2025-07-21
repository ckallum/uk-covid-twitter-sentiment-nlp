import json
import numpy as np
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.shared import get_data_sources, SENTIMENT_DROPDOWN_VALUE_TO_PREDICTIONS
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

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Get sentiment bar chart data"""
        try:
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            date = query_params.get('date', [None])[0]
            source = query_params.get('source', ['covid'])[0]
            nlp_type = query_params.get('nlp_type', ['nn'])[0]
            
            if not date:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Date parameter is required'}).encode())
                return
            
            data_sources = get_data_sources()
            geo_df = data_sources['geo_df_data_sources'][source]
            predictions = SENTIMENT_DROPDOWN_VALUE_TO_PREDICTIONS[nlp_type]
            
            fig = plot_sentiment_bar(geo_df, date, predictions)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(fig_to_json(fig)).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode()) 