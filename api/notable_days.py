import json
import numpy as np
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.shared import get_data_sources

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Get notable days data"""
        try:
            # Parse query parameters
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            topic = query_params.get('topic', ['covid'])[0]
            nlp_type = query_params.get('nlp_type', ['vader'])[0]
            
            # Get data sources
            data_sources = get_data_sources()
            
            # For now, return basic response without complex plotting
            response_data = {
                'status': 'success',
                'topic': topic,
                'nlp_type': nlp_type,
                'message': 'Notable days endpoint working',
                'data_loaded': len(data_sources) > 0
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode()) 