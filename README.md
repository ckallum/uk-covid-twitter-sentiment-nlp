# COVID-19 Sentiment Analysis in the UK

A web application that analyzes and visualizes sentiment towards COVID-19 and lockdown in the UK based on Twitter data.

![Dashboard Preview](static/assets/dashboard_preview.png)

## Introduction

This project analyzes the sentiment of tweets within the UK during the COVID-19 pandemic to examine correlations with news events and how sentiment differed across UK regions over time. The dashboard provides interactive visualizations to explore these patterns and trends.

## Features

- Interactive timeline exploration of sentiment across UK counties
- Analysis of tweet sentiment using multiple NLP techniques:
  - Vader
  - TextBlob
  - LSTM
  - Naive Bayes
- Comparison of sentiment across different UK regions
- Correlation between sentiment, COVID-19 case numbers, and deaths
- Visualization of popular hashtags and emojis
- Display of important news events

## Project Structure

```
covid-sentiment-nlp-uk/
├── api.py              # Flask API endpoints
├── app.py              # Original Dash application (deprecated)
├── assets/             # Wordcloud images and styles
├── data/               # Dataset files
│   ├── covid/          # COVID tweets analysis data
│   ├── covid-data/     # COVID statistics
│   ├── events/         # News and events timeline
│   ├── geojson/        # UK geographical data
│   └── lockdown/       # Lockdown tweets analysis data
├── requirements.txt    # Python dependencies
├── serve.py            # Web application server
├── static/             # Static web assets
│   ├── assets/         # Images and other assets
│   ├── css/            # Stylesheets
│   ├── js/             # JavaScript files
│   └── index.html      # Main HTML page
└── utils/              # Utility functions
    ├── aggregations.py # Data aggregation functions
    ├── formatting.py   # Data formatting functions
    └── plotting.py     # Plotting functions
```

## Technologies Used

- **Frontend**: HTML, CSS, JavaScript, Plotly.js
- **Backend**: Python, Flask, Pandas, Plotly
- **Data Analysis**: Sentiment analysis techniques (Vader, TextBlob, LSTM, Naive Bayes)

## Data Sources

- **Twitter Data**: Collected using SNScrape, containing tweets related to COVID and lockdown in the UK
- **COVID Statistics**: Public Health England (coronavirus.data.gov.uk)
- **News Events**: The Guardian News API

## Installation and Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/covid-sentiment-nlp-uk.git
cd covid-sentiment-nlp-uk
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:

```bash
pip install -r requirements.txt
```

4. Run the application:

```bash
python serve.py
```

5. Open your browser and visit:

```
http://localhost:8080
```

## Using the Dashboard

### Navigation

- Use the sidebar to navigate between the different sections:
  - **Home**: Overview of the dashboard and data sources
  - **Timeline Exploration**: Interactive timeline with maps and charts
  - **Data Analysis**: Analysis of sentiment and correlations

### Timeline Exploration

- Use the date slider or navigation buttons to explore data on different dates
- Toggle different visualizations on/off using the checkboxes
- Switch between COVID and lockdown datasets
- Choose different sentiment analysis techniques from the dropdown

### Data Analysis

- View notable days with extreme sentiment values
- Compare different sentiment analysis techniques
- Explore correlations between sentiment, case numbers, and deaths

## Deployment Options

This application has been designed with a clean separation between frontend and backend, making it easy to deploy in various ways:

### Option 1: Full Stack Deployment

Deploy both the Python backend and the web frontend together on platforms like:
- Heroku
- PythonAnywhere
- AWS Elastic Beanstalk

### Option 2: Static Frontend + API Backend

- Deploy the static files (HTML, CSS, JS) on a web server or CDN
- Host the Flask API separately on a Python-compatible hosting service

### Option 3: Containerization

Package the application with Docker:

```bash
# Sample Dockerfile (create this in the project root)
FROM python:3.8-slim

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

EXPOSE 8080
CMD ["python", "serve.py"]
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Data was collected using SNScrape from Twitter, Public Health England, and The Guardian
- Special thanks to all open-source libraries used in this project