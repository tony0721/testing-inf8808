import json

import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State

import plotly.graph_objects as go

from viz4 import getRecommendationsForDecade

app = dash.Dash(__name__)
app.title = 'Spotify Song Recommender'

# TODO - Use the real preference instead of this dummy one
dict_pref = {
    'sous_genres' : ['trap','neo soul','tropical'],
    'artistes': ['Ed Sheeran','Metallica','Drake']
}

app.layout = html.Div(getRecommendationsForDecade(2010, 2019, dict_pref))

server = app.server