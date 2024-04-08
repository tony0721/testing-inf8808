import dash_html_components as html
import dash
from dash import callback, Input, Output
from dash import State
import helpers
import pandas as pd

helper = helpers.Helper("./data/spotify_songs.csv")
maxYear = 2019
minYear = 1970

dict_pref_cache = None

@callback(
    Output('viz4-container', 'children'),
    [Input('generate-decade-button', 'n_clicks'), Input('generate-decade-button-2', 'n_clicks')],
    [State('generate-decade-button', 'value'), State('generate-decade-button-2', 'value')]
)
def generate_decade_recommendations(n_clicks, n_clicks2 ,value, value2):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    if ctx.triggered[0]['prop_id'] == 'generate-decade-button.n_clicks':
        return handleDecadeChange(n_clicks, value)
    if ctx.triggered[0]['prop_id'] == 'generate-decade-button-2.n_clicks':
        return handleDecadeChange(n_clicks2, value2)

explorationString1 = "Exploration de vos potentiels"
explorationString2 = "goûts musicaux pour la décennie:"
incontournableString = "Vos incontournables"

def getRecommendationsForDecade(startYear, endYear, dict_pref):
    global dict_pref_cache
    dict_pref_cache = None
    if dict_pref_cache is None:
        dict_pref_cache = dict_pref
    # Only show the buttons if can go up or down.
    buttonDownVisible = "visible" if startYear > minYear else "hidden"
    buttonUpVisible = "visible" if endYear < maxYear else "hidden"
    
    return html.Div(id="viz4-container", className="column",children = [
        html.Div(id="viz4", children = [
            getVisualisation4Component(startYear, endYear, dict_pref),
        ]),
        html.Div(className="decade-button-container", children = [
            html.Button('▼', id='generate-decade-button', className='generate-decade-button', value=f'{startYear-10}-{endYear-10}', style={'visibility': buttonDownVisible}),
            html.Button('▲', id='generate-decade-button-2', className='generate-decade-button', value=f'{startYear+10}-{endYear+10}', style={'visibility': buttonUpVisible})        
        ]),
])
    
def getVisualisation4Component(startYear, endYear, dict_pref):
    
    decadeString = str(endYear) + " - " + str(startYear)
    
    return html.Div(className="column", children = [
            html.Div(className="flex-container-space-between", children = [
                html.Div(className="title", children=[
                    html.H1([explorationString1, html.Br(), explorationString2], style={'margin-top': '15px'})
                ]),
                html.Div(className="column", children=[
                    html.Div(id="decade-text", children=decadeString),
                    html.Div(className="flex-container", children = [
                        html.Div(incontournableString, className="incontournable-text"),
                        html.Img(src='assets/star.png', className="star-icon")
                    ])
                ])
            ]),
            getDecadeContentComponents(dict_pref, startYear, endYear),
        ])
    
def getDecadeContentComponents(dict_pref, startYear, endYear):    
    return html.Div(className="flex-container-space-between", children=[
        getTimelineComponent(startYear, endYear, dict_pref),
        html.Div(className="flex-container", style={'width': '50%'}, children=[
            getListOfRecommendationsComponents(get_top_artists_for_decade(startYear, endYear, dict_pref), "artist",width='70%'),
            getListOfRecommendationsComponents(get_top_genre_for_decade(startYear, endYear, dict_pref), "genres", width='70%') 
        ])
    ])


def getTimelineComponent(startYear, endYear, dict_pref):
    timeline_items = []

    songsInfo = get_top_songs_for_decade(startYear, endYear, dict_pref)

    for song_name, year, isBest, artist, album_name, similarity in songsInfo:
        details = "This song was released in " + str(year) + " by " + artist + " in the album " + album_name + ". This song matches your profile by " + str(round(similarity*100, 2)) + "%"
        
        timeline_item_content = [
            html.Div(year, className='timeline-year'),
            html.Div(song_name, className='timeline-song', title=details)
        ]
     
        if isBest:
            timeline_item_content.append(html.Img(src="assets/star.png", className="star-icon"))
        else:
            timeline_item_content.append(html.Div(className="transparent-star"))

        timeline_item = html.Div(timeline_item_content, className='timeline-item')
        timeline_items.append(timeline_item)


    timeline_container = html.Div(timeline_items, className='timeline-container')

    return timeline_container

    
def getListOfRecommendationsComponents(recommendations, id_suffix, width='50%'): 
    recommendations_components = []
    for name, isBest in recommendations:
        if isBest:
            recommendation_component = html.Span([
                name,
                html.Img(src="assets/star.png", className="star-icon")
            ])
        else:
            recommendation_component = html.Span([
                name,
                html.Div(className="transparent-star")
            ])

        recommendations_components.append(html.P(recommendation_component, className='recommendation'))

    return html.Div(
        id=f'recommendations-div-{id_suffix}',
        children=recommendations_components,
        className='recommendations-column',
        style={'width': width}
    )


def handleDecadeChange(n_clicks, value):
    if n_clicks is None:
        return dash.no_update

    start_year, end_year = value.split('-')
    start_year = int(start_year)
    end_year = int(end_year)
    
    if end_year < minYear or end_year > maxYear:
        return dash.no_update
    
    global dict_pref_cache 
    if dict_pref_cache is None:
        return dash.no_update
    
    return getRecommendationsForDecade(start_year, end_year, dict_pref_cache)


# Helper functions to get the top songs
# Needs to return an array containing a song, its year, if it is the favorite and details for each songs
def get_top_songs_for_decade(start_year, end_year, dict_pref):
    song_recommendations = helper.generate_yearly_song_recommendation(dict_pref)
    songInDecade = pd.DataFrame()
    
    for year in range(start_year, end_year + 1):
        yearly_data = song_recommendations[song_recommendations['year'] == year]
        if not yearly_data.empty:
            songInDecade = pd.concat([songInDecade, yearly_data])

    # Find the entry with the highest score
    bestSong = songInDecade.sort_values(by='similarity', ascending=False).head(1)
    songInDecade = songInDecade.sort_values(by='year', ascending=False).head(10).reset_index(drop=True)
    
    songOfTheDecade = []
    for index, row in songInDecade.iterrows():
        isBest = row["similarity"] == bestSong["similarity"].values[0]
        songOfTheDecade.append((row['track_name'], row['year'], isBest, row['track_artist'], row['track_album_name'], row['similarity']))

    return songOfTheDecade

def get_top_artists_for_decade(start_year, end_year, dict_pref):
    artist_recommendations = helper.generate_yearly_artist_recommendation(dict_pref)
    artistsInDecade = pd.DataFrame()
    
    for year in range(start_year, end_year + 1):
        yearly_data = artist_recommendations[artist_recommendations['year'] == year]
        if not yearly_data.empty:
            artistsInDecade = pd.concat([artistsInDecade, yearly_data])
    
    # Remove duplicates
    artistsInDecade = artistsInDecade.drop_duplicates(subset=['track_artist'])
    
    artistsInDecade = artistsInDecade.sort_values(by='similarity', ascending=False).head(5).reset_index(drop=True)
    bestArtist = artistsInDecade.sort_values(by='similarity', ascending=False).head(1)
    
    artistsOfTheDecade = []
    for index, row in artistsInDecade.iterrows():
        isBest = row["similarity"] == bestArtist["similarity"].values[0]
        artistsOfTheDecade.append((row['track_artist'], isBest))
    print(artistsOfTheDecade)
    return artistsOfTheDecade

def get_top_genre_for_decade(start_year, end_year, dict_pref):
    genre_recommendations = helper.generate_yearly_genre_recommendation(dict_pref)
    genresInDecade = pd.DataFrame()
    
    for year in range(start_year, end_year + 1):
        yearly_data = genre_recommendations[genre_recommendations['year'] == year]
        if not yearly_data.empty:
            genresInDecade = pd.concat([genresInDecade, yearly_data])
    
    # Remove duplicates
    genresInDecade = genresInDecade.drop_duplicates(subset=['playlist_genre'])
    
    bestGenre = genresInDecade.sort_values(by='similarity', ascending=False).head(1)
    genresInDecade = genresInDecade.sort_values(by='similarity', ascending=False).head(5).reset_index(drop=True)
    
    genresOfTheDecade = []
    for index, row in genresInDecade.iterrows():
        isBest = row["similarity"] == bestGenre["similarity"].values[0]
        genresOfTheDecade.append((row['playlist_genre'], isBest))
    print(genresInDecade)
    return genresOfTheDecade