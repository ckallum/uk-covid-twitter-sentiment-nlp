"""
Simple server to run the web application
"""
from api import app

if __name__ == '__main__':
    app.run(debug=True, port=8080)