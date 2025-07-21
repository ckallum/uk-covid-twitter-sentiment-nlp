# Deploying COVID-19 Sentiment Dashboard to Vercel

This guide will help you deploy your COVID-19 Sentiment Analysis dashboard to Vercel.

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Vercel CLI**: Install the Vercel CLI
   ```bash
   npm i -g vercel
   ```
3. **Git Repository**: Your code should be in a Git repository (GitHub, GitLab, or Bitbucket)

## Project Structure for Vercel

The project has been restructured for Vercel deployment:

```
covid-sentiment-nlp-uk/
├── api/                    # Serverless functions
│   ├── __init__.py
│   ├── shared.py          # Shared data loading utilities
│   ├── dates.py           # /api/dates endpoint
│   ├── covid_stats.py     # /api/covid_stats endpoint
│   ├── county_choropleth.py # /api/county_choropleth endpoint
│   ├── sentiment_bar_chart.py # /api/sentiment_bar_chart endpoint
│   └── notable_days.py    # /api/notable_days endpoint
├── data/                  # Dataset files
├── utils/                 # Utility functions
├── assets/                # Static assets (moved from static/)
├── css/                   # Stylesheets (moved from static/)
├── js/                    # JavaScript files (moved from static/)
├── index.html             # Main HTML (moved from static/)
├── vercel.json            # Vercel configuration
├── requirements.txt       # Python dependencies
└── README.md
```

## Deployment Steps

### Option 1: Deploy via Vercel CLI (Recommended)

1. **Login to Vercel**:
   ```bash
   vercel login
   ```

2. **Navigate to your project directory**:
   ```bash
   cd covid-sentiment-nlp-uk
   ```

3. **Deploy to Vercel**:
   ```bash
   vercel
   ```
   
   Follow the prompts:
   - Link to existing project? **N**
   - What's your project's name? **covid-sentiment-dashboard** (or your preferred name)
   - In which directory is your code located? **./** 
   - Want to override the settings? **N**

4. **Deploy to production**:
   ```bash
   vercel --prod
   ```

### Option 2: Deploy via Git Integration

1. **Push your code to GitHub/GitLab/Bitbucket**

2. **Import project in Vercel Dashboard**:
   - Go to [vercel.com/dashboard](https://vercel.com/dashboard)
   - Click "New Project"
   - Import your repository
   - Configure build settings (should auto-detect)
   - Deploy

## Configuration Files

### vercel.json
```json
{
  "functions": {
    "api/*.py": {
      "runtime": "@vercel/python"
    }
  },
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "/api/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/$1"
    }
  ]
}
```

### requirements.txt
Make sure your `requirements.txt` includes all dependencies:
```
pandas>=1.3.0
plotly>=5.0.0
numpy>=1.21.0
pathlib2>=2.3.0
```

## API Endpoints Structure

Your API endpoints are now serverless functions:

- `/api/dates` - Get available dates
- `/api/covid_stats` - Get COVID statistics
- `/api/county_choropleth` - Get map data
- `/api/sentiment_bar_chart` - Get sentiment charts
- `/api/notable_days` - Get notable days analysis

## Troubleshooting

### Common Issues

1. **Import Errors**: 
   - Make sure all imports use relative paths in API functions
   - Verify `utils/` module is properly structured

2. **Data Loading Issues**:
   - Ensure all data files are included in your repository
   - Check file paths in `api/shared.py`

3. **Function Timeout**:
   - Vercel has a 10-second timeout for Hobby plan
   - Consider optimizing data loading or upgrading plan

### Environment Variables

If you need environment variables:

1. **Via Vercel CLI**:
   ```bash
   vercel env add VARIABLE_NAME
   ```

2. **Via Dashboard**:
   - Go to Project Settings → Environment Variables
   - Add your variables

### Monitoring

- Check function logs in Vercel Dashboard
- Monitor performance and usage
- Set up custom domains if needed

## Post-Deployment

1. **Test all functionality**:
   - Navigate through different sections
   - Test date selection and filtering
   - Verify all charts load correctly

2. **Custom Domain** (Optional):
   - Add custom domain in Vercel Dashboard
   - Configure DNS settings

3. **Analytics** (Optional):
   - Enable Vercel Analytics
   - Set up monitoring

## Performance Considerations

- **Cold Starts**: First request may be slower due to data loading
- **Data Caching**: Consider implementing caching for frequently accessed data
- **File Size**: Large datasets may impact deployment size

## Support

- **Vercel Documentation**: [vercel.com/docs](https://vercel.com/docs)
- **Vercel Community**: [github.com/vercel/vercel/discussions](https://github.com/vercel/vercel/discussions)

## Cost Considerations

- **Hobby Plan**: Free tier with limitations
- **Pro Plan**: $20/month with higher limits
- **Function execution time and bandwidth usage count toward limits 