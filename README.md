## Introduction
The aim of this project is to look at sentiment of tweets within the UK during the period of a year when Covid-19 was present and see if there was a correlation to certain news articles, and how different regions within the UK differed over time. 

## Downloading and running

Clone or download the repository.

```bash
python -m venv venv
source venv/bin/activate  # Windows: \venv\scripts\activate
pip install -r requirements.txt
```

then run the app:
```bash
python app.py
```

## Deploy to Heroku

All pushes to the main branch are automatically deployed to Heroku here: https://covid-19-uk-twitter-sentiment.herokuapp.com/.

Debug some problems using
```bash
heroku logs --tail
```
