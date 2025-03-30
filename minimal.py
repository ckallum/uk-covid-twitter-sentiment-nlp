"""
Minimal Flask application for Heroku deployment testing
"""
import os
from flask import Flask, jsonify, send_from_directory
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
    favicon_paths = [
        BASE_DIR / 'static/assets/favicon.ico',
        BASE_DIR / 'assets/favicon.ico'
    ]
    
    return jsonify({
        "status": "ok",
        "base_dir": str(BASE_DIR),
        "favicon_paths": {
            str(path): path.exists() for path in favicon_paths
        }
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
    """Minimal index page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>COVID Sentiment Analysis - Minimal Test</title>
        <link rel="icon" href="/favicon.ico" type="image/x-icon">
    </head>
    <body>
        <h1>COVID Sentiment Analysis - Minimal Test</h1>
        <p>This is a minimal test page to verify the app is running on Heroku.</p>
        <p>Check the <a href="/health">health</a> and <a href="/debug">debug</a> endpoints.</p>
    </body>
    </html>
    """

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)