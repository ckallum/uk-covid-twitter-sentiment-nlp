import plotly.express as px
import json
import numpy as np
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.shared import load_data, get_data_sources, SENTIMENT_DROPDOWN_VALUE_TO_AVG_SCORE

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
    
    # First convert to JSON string then back to dict to ensure Python native types
    sanitized_dict = json.loads(json.dumps(fig_dict, cls=NumpyEncoder))
    
    return {
        'data': sanitized_dict['data'],
        'layout': sanitized_dict['layout']
    }

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Get county choropleth map data"""
        try:
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            date = query_params.get('date', [None])[0]
            nlp_type = query_params.get('nlp_type', ['nn'])[0]
            topic = query_params.get('topic', ['covid'])[0]
            
            if not date:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Date parameter is required'}).encode())
                return
            
            data = load_data()
            data_sources = get_data_sources()
            
            geo_df = data_sources['geo_df_data_sources'][topic]
            color = SENTIMENT_DROPDOWN_VALUE_TO_AVG_SCORE[nlp_type]
            
            geo_df = geo_df.loc[geo_df['date'] == date]
            fig = px.choropleth_mapbox(
                geo_df,
                locations="id",
                geojson=data['uk_counties'],
                color=color,
                hover_name="county",
                hover_data=["vader-score_avg", "textblob-score_avg", "nn-score_avg"],
                color_continuous_scale="RdYlGn",
                range_color=[-1, 1],
                mapbox_style="carto-positron",
                zoom=4.8,
                center={"lat": 55.3781, "lon": -3.4360},
                opacity=0.5,
                labels={color: 'Sentiment Score'},
            )
            fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(fig_to_json(fig)).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode()) 