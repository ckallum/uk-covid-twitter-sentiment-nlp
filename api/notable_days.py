import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Get notable days data"""
        try:
            # Parse query parameters
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            topic = query_params.get('topic', ['covid'])[0]
            nlp_type = query_params.get('nlp_type', ['vader'])[0]
            
            # Return mock data for now
            response_data = {
                'status': 'success',
                'topic': topic,
                'nlp_type': nlp_type,
                'message': 'Notable days endpoint working without dependencies',
                'mock_data': True,
                'notable_days': [
                    {'date': '2020-03-23', 'event': 'UK Lockdown Announced', 'sentiment': -0.5},
                    {'date': '2020-05-10', 'event': 'Stay Alert Message', 'sentiment': -0.2},
                    {'date': '2020-12-08', 'event': 'First Vaccine', 'sentiment': 0.7}
                ]
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