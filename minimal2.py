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
    # Check both case variations (case sensitive vs case insensitive filesystems)
    data_files = [
        'data/geojson/uk_counties_simpler.json',
        'data/Geojson/uk_counties_simpler.json',
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
    
    # List directories to see what's available (checking both case variations)
    dir_variations = {
        'data': ['data'],
        'data/covid': ['data/covid'],
        'data/geojson': ['data/geojson', 'data/Geojson', 'data/GeoJSON']
    }
    
    dir_listing = {}
    for dir_key, variations in dir_variations.items():
        for variant in variations:
            path = BASE_DIR / variant
            if path.exists():
                dir_listing[variant] = os.listdir(path)
                break
        if dir_key not in dir_listing:
            dir_listing[dir_key] = []
    
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
        # Try different case variations of the path
        case_variations = [
            'data/geojson/uk-district-list-all.csv',
            'data/Geojson/uk-district-list-all.csv'
        ]
        
        result = {'status': 'loading', 'checked_paths': []}
        
        counties_path = None
        for path_str in case_variations:
            path = BASE_DIR / path_str
            result['checked_paths'].append({'path': str(path), 'exists': path.exists()})
            if path.exists():
                counties_path = path
                break
        
        if counties_path:
            # Try to load the counties data
            counties_df = pd.read_csv(counties_path)
            counties = counties_df['county'].tolist()
            result['counties'] = counties[:10]  # Show first 10 counties
            result['status'] = 'success'
            result['used_path'] = str(counties_path)
        else:
            result['error'] = f"File not found in any of the checked paths"
        
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

@app.route('/list-files')
def list_files():
    """List all data files recursively"""
    try:
        data_path = BASE_DIR / 'data'
        
        def walk_directory(path):
            result = []
            if not path.exists():
                return result
            
            for item in path.iterdir():
                if item.is_file():
                    result.append(str(item.relative_to(BASE_DIR)))
                elif item.is_dir():
                    result.extend(walk_directory(item))
            return result
        
        all_files = walk_directory(data_path)
        return jsonify({
            'status': 'success',
            'file_count': len(all_files),
            'files': all_files
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        })

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
            <a href="/list-files" class="btn">List All Files</a>
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)