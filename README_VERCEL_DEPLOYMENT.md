# COVID Sentiment NLP UK - Vercel Deployment Guide

This guide explains how to deploy the COVID-19 sentiment analysis application to Vercel.

## Project Structure

The project has been restructured for Vercel deployment:

```
├── api/                    # Serverless functions (Python)
│   ├── dates.py           # Get available date ranges
│   ├── covid_stats.py     # COVID statistics data
│   ├── county_choropleth.py # Geographic data
│   ├── sentiment_bar_chart.py # Sentiment charts
│   ├── notable_days.py    # Notable events data
│   └── shared.py          # Shared utilities and data loading
├── static files moved to root for direct serving
├── vercel.json            # Vercel configuration
├── .vercelignore          # Files to exclude from deployment
└── requirements.txt       # Minimal Python dependencies
```

## Configuration Files

### vercel.json
```json
{
  "functions": {
    "api/*.py": {
      "excludeFiles": "{data/**,static/**,assets/**,venv/**,*.png,*.jpg,*.pdf,README.md,CONTRIBUTING.md,minimal.py,minimal2.py,app.py,serve.py,robust_api.py,wsgi.py,Procfile,runtime.txt}"
    }
  },
  "routes": [
    { "src": "/api/(.*)", "dest": "/api/$1" },
    { "src": "/(.*)", "dest": "/$1" }
  ]
}
```

### .vercelignore
```
data/
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.env
.venv
ENV/
env.bak/
venv.bak/
.pytest_cache/
.coverage
htmlcov/
.tox/
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.DS_Store
Thumbs.db
*.log
ads_figures_and_tables.pdf
assets/
static/assets/
```

### requirements.txt (Optimized)
Only essential packages to keep function size under 250MB:
```
Flask==2.2.5
pandas==2.2.2
plotly==5.21.0
numpy==1.26.4
requests==2.32.3
python-dateutil==2.9.0
```

## Deployment Steps

1. **Install Vercel CLI**:
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Deploy**:
   ```bash
   vercel --prod
   ```

## Data Loading Strategy

Due to Vercel's 250MB function size limit, data files are loaded from GitHub raw URLs:
- Small essential data files are loaded on startup
- Large datasets (like geographic data) are loaded on-demand
- Falls back to local files if URL loading fails

## Troubleshooting

### ✅ FIXED: sklearn/scikit-learn Import Error
**Error**: `ModuleNotFoundError: No module named 'sklearn'`

**Solution**: Removed unused imports from `api/shared.py` that were importing `utils.formatting` functions, which in turn imported `sklearn`. These formatting functions weren't actually used in any API endpoints.

### Function Size Limit (250MB)
If you encounter size errors:
1. Check `vercel.json` excludeFiles patterns
2. Verify `.vercelignore` is comprehensive
3. Consider removing unused dependencies from `requirements.txt`
4. Move large data files to external hosting (GitHub raw, Vercel Blob, etc.)

### Build Failures
- Ensure Python version compatibility
- Check that all required dependencies are in `requirements.txt`
- Verify file paths in serverless functions

## Current Status: ✅ DEPLOYED

The application should now be successfully deployed to Vercel with:
- ✅ Function size under 250MB limit
- ✅ All Python dependencies resolved
- ✅ Data loading from external URLs
- ✅ Static file serving working

## API Endpoints

All endpoints are available at `https://your-app.vercel.app/api/`:
- `/api/dates` - Available date ranges
- `/api/covid_stats` - COVID statistics
- `/api/county_choropleth` - Geographic sentiment data
- `/api/sentiment_bar_chart` - Sentiment analysis charts  
- `/api/notable_days` - Notable events and days 