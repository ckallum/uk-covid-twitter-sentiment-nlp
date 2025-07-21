import plotly.express as px
import json
import numpy as np
from .shared import load_data, get_data_sources, SENTIMENT_DROPDOWN_VALUE_TO_AVG_SCORE

def fig_to_json(fig):
    """Convert a plotly figure to a JSON representation for the API"""
    fig_dict = fig.to_dict()
    
    class NumpyEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, np.integer):
                return int(obj)
            if isinstance(obj, np.floating):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            return super(NumpyEncoder, self).default(obj)
    
    # First convert to JSON string then back to dict to ensure Python native types
    sanitized_dict = json.loads(json.dumps(fig_dict, cls=NumpyEncoder))
    
    return {
        'data': sanitized_dict['data'],
        'layout': sanitized_dict['layout']
    }

def handler(request):
    """Get county choropleth map data"""
    try:
        date = request.args.get('date')
        nlp_type = request.args.get('nlp_type', 'nn')
        topic = request.args.get('topic', 'covid')
        
        if not date:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Date parameter is required'})
            }
        
        data = load_data()
        data_sources = get_data_sources()
        
        geo_df = data_sources['geo_df_data_sources'][topic]
        color = SENTIMENT_DROPDOWN_VALUE_TO_AVG_SCORE[nlp_type]
        
        geo_df = geo_df.loc[geo_df['date'] == date]
        fig = px.choropleth_mapbox(
            geo_df,
            locations="id",
            geojson=data['uk_counties'],
            color=color,
            hover_name="county",
            hover_data=["vader-score_avg", "textblob-score_avg", "nn-score_avg"],
            color_continuous_scale="RdYlGn",
            range_color=[-1, 1],
            mapbox_style="carto-positron",
            zoom=4.8,
            center={"lat": 55.3781, "lon": -3.4360},
            opacity=0.5,
            labels={color: 'Sentiment Score'},
        )
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(fig_to_json(fig))
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        } 