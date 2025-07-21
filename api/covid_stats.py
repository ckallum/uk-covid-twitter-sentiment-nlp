import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.shared import load_data

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Get COVID stats for a given date"""
        try:
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            date = query_params.get('date', [None])[0]
            if not date:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Date parameter is required'}).encode())
                return
                
            data = load_data()
            df_covid_stats = data['df_covid_stats']
            
            total_deaths = df_covid_stats.loc[df_covid_stats['date'] == date, 'cumDeathsByDeathDate'].sum()
            total_cases = df_covid_stats.loc[df_covid_stats['date'] == date, 'cumCasesByPublishDate'].sum()
            
            response_data = {
                'date': date,
                'total_deaths': int(total_deaths),
                'total_cases': int(total_cases)
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