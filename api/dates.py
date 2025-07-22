import json
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Return all dates in the dataset"""
        try:
            # Generate date list using simple datetime operations
            from datetime import datetime, timedelta
            
            start_date = datetime(2020, 3, 20)
            end_date = datetime(2021, 3, 25)
            
            dates_list = []
            current_date = start_date
            while current_date <= end_date:
                dates_list.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=1)
            
            response_data = {
                'dates': dates_list,
                'start_date': '2020-03-20',
                'end_date': '2021-03-25',
                'status': 'working without external dependencies',
                'total_dates': len(dates_list)
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