"""
Second step towards full app - with minimal data loading
"""
import os
import json
import pandas as pd
from flask import Flask, jsonify, send_from_directory, render_template_string
from pathlib import Path

# Create the Flask app
app = Flask(__name__)

# Define the base directory
BASE_DIR = Path(__file__).resolve().parent

@app.route('/health')
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "ok"})

@app.route('/debug')
def debug():
    """Debug endpoint to check file paths"""
    # Check for critical data files
    data_files = [
        'data/geojson/uk_counties_simpler.json',
        'data/covid-data/uk_covid_stats.csv',
        'data/covid-data/r_numbers.csv',
        'data/covid/top_ten_hashtags_per_day.csv'
    ]
    
    file_info = {}
    for path in data_files:
        full_path = BASE_DIR / path
        file_info[path] = {
            'exists': full_path.exists(),
            'size': full_path.stat().st_size if full_path.exists() else 0
        }
    
    # List directories to see what's available
    dir_listing = {
        'data': os.listdir(BASE_DIR / 'data') if (BASE_DIR / 'data').exists() else [],
        'data/covid': os.listdir(BASE_DIR / 'data/covid') if (BASE_DIR / 'data/covid').exists() else [],
        'data/geojson': os.listdir(BASE_DIR / 'data/geojson') if (BASE_DIR / 'data/geojson').exists() else []
    }
    
    return jsonify({
        "status": "ok",
        "base_dir": str(BASE_DIR),
        "file_info": file_info,
        "directories": dir_listing
    })

@app.route('/test-data')
def test_data():
    """Try to load just one data file"""
    try:
        counties_path = BASE_DIR / 'data/geojson/uk-district-list-all.csv'
        result = {'status': 'loading'}
        
        if counties_path.exists():
            # Try to load the counties data
            counties_df = pd.read_csv(counties_path)
            counties = counties_df['county'].tolist()
            result['counties'] = counties[:10]  # Show first 10 counties
            result['status'] = 'success'
        else:
            result['error'] = f"File not found: {counties_path}"
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'type': str(type(e))
        })

@app.route('/favicon.ico')
def favicon():
    """Serve favicon directly"""
    for path in [BASE_DIR / 'static/assets', BASE_DIR / 'assets']:
        if (path / 'favicon.ico').exists():
            return send_from_directory(path, 'favicon.ico')
    
    # Fallback
    return "", 204

@app.route('/')
def index():
    """Minimal index page with test links"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>COVID Sentiment Analysis - Testing Data Loading</title>
        <link rel="icon" href="/favicon.ico" type="image/x-icon">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            h1 { color: #2c3e50; }
            .container { max-width: 800px; margin: 0 auto; }
            .btn { 
                display: inline-block; 
                padding: 10px 20px; 
                background: #3498db; 
                color: white; 
                text-decoration: none; 
                border-radius: 4px; 
                margin: 10px 5px;
            }
            .btn:hover { background: #2980b9; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>COVID Sentiment Analysis - Testing Data Loading</h1>
            <p>This page tests data loading functionality to identify Heroku deployment issues.</p>
            
            <h2>Test Endpoints</h2>
            <a href="/health" class="btn">Health Check</a>
            <a href="/debug" class="btn">Debug Info</a>
            <a href="/test-data" class="btn">Test Data Loading</a>
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)