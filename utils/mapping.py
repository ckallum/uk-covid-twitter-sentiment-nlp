import pandas as pd
import time
import numpy as np
from plotly.subplots import make_subplots

from skimage import io
from utils.plotting import format_df_ma_stats, plot_covid_stats, create_event_array

df_events = pd.read_csv('../data/events/key_events.csv', skipinitialspace=True, usecols=['Date', 'Event'])
start_global = '2020-03-20'
end_global = '2021-03-19'
df_covid_stats = pd.read_csv('../data/COVID-Dataset/uk_covid_stats.csv', skipinitialspace=True)
dates_list = [str(date.date()) for date in pd.date_range(start=start_global, end=end_global).tolist()]

events_array = create_event_array(df_events, start_global, end_global)

# Define frames
import plotly.graph_objects as go

fig = go.Figure(frames=[go.Frame(data=[
    plot_covid_stats(format_df_ma_stats(df_covid_stats, ['England'], start_global, date)
                     , events_array, 'England')[1],
    plot_covid_stats(format_df_ma_stats(df_covid_stats, ['England'], start_global, date)
                     , events_array, 'England')[0]],
    name=str(i)  # you need to name the frame for the animation to behave properly
)
    for i, date in enumerate(dates_list)],
)

fig.add_trace(plot_covid_stats(
    format_df_ma_stats(df_covid_stats, ['England'], start_global, start_global), events_array, 'England')[0]
              )
fig.add_trace(plot_covid_stats(
    format_df_ma_stats(df_covid_stats, ['England'], start_global, start_global), events_array, 'England')[1]
              )

def frame_args(duration):
    return {
        "frame": {"duration": duration},
        "mode": "immediate",
        "fromcurrent": True,
        "transition": {"duration": duration, "easing": "linear"},
    }


sliders = [
    {
        "pad": {"b": 10, "t": 60},
        "len": 0.9,
        "x": 0.1,
        "y": 0,
        "steps": [
            {
                "args": [[f.name], frame_args(0)],
                "label": str(k),
                "method": "animate",
            }
            for k, f in enumerate(fig.frames)
        ],
    }
]

# Layout
fig.update_layout(
    title='Slices in volumetric data',
    width=600,
    height=600,
    scene=dict(
        zaxis=dict(range=[-0.1, 6.8], autorange=False),
        aspectratio=dict(x=1, y=1, z=1),
    ),
    updatemenus=[
        {
            "buttons": [
                {
                    "args": [None, frame_args(50)],
                    "label": "&#9654;",  # play symbol
                    "method": "animate",
                },
                {
                    "args": [[None], frame_args(0)],
                    "label": "&#9724;",  # pause symbol
                    "method": "animate",
                },
            ],
            "direction": "left",
            "pad": {"r": 10, "t": 70},
            "type": "buttons",
            "x": 0.1,
            "y": 0,
        }
    ],
    sliders=sliders
)

fig.show()
import time
import numpy as np
