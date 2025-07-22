import json
import pandas as pd
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.shared import load_data

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Return all dates in the dataset"""
        try:
            data = load_data()
            
            # Dates
            start_global = '2020-03-20'
            end_global = '2021-03-25'
            dates_list = pd.date_range(start=start_global, end=end_global)
            str_dates_list = [str(date.date()) for date in dates_list]
            
            response_data = {
                'dates': str_dates_list,
                'start_date': start_global,
                'end_date': end_global,
                'status': 'restored full functionality'
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