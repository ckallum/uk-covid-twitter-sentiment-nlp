import json
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Return all dates in the dataset"""
        try:
            response_data = {
                'dates': ['2020-03-20', '2020-03-21', '2020-03-22'],
                'start_date': '2020-03-20',
                'end_date': '2021-03-25',
                'status': 'working minimal',
                'message': 'Basic test'
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