import json
import numpy as np
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.shared import get_data_sources
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

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Get notable days chart data"""
        try:
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            topic = query_params.get('topic', ['covid'])[0]
            nlp_type = query_params.get('nlp_type', ['nn'])[0]
            
            data_sources = get_data_sources()
            notable_days_df = data_sources['notable_days_sources'][topic]
            
            fig = plot_notable_days(notable_days_df, nlp_type)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(fig_to_json(fig)).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode()) 