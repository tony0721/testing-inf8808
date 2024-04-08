#%%
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from scipy.spatial import distance

class Helper:
    """ 
        Exemple: 

    dict_pref = {
        'sous_genres' : ['trap','neo soul','tropical'],
        'artistes': ['Ed Sheeran','Metallica','Drake']
    }

    path_name = './data/spotify_songs.csv'

    help = Helper(path_name)
    df_data = help.df_data

    user_pref_dict = help.generate_user_preferences_dict(dict_pref)
    print("User Preferences Dictionary:")
    print(user_pref_dict)

    # Generate a dictionary with average preferences across all data
    average_pref_dict = help.generate_average_preferences_dict()
    print("\nAverage Preferences Dictionary:")
    print(average_pref_dict)

    # Generate a DataFrame showing similarity between user preferences and subgenres
    subgenre_similarity_df = help.generate_subgenre_similarity_df(dict_pref)
    print("\nSubgenre Similarity DataFrame:")
    print(subgenre_similarity_df.head()) 

    recommendations_df, mean_pref_values = help.generate_recommendations_df(dict_pref, recommendation_type='chansons')
    print("\nRecommendations DataFrame:")
    print(recommendations_df.head()) 
    print("\nMean Preferences Values for Recommendations:")
    print(mean_pref_values)

    print("\nYearly artist recommendation:")
    print(help.generate_yearly_artist_recommendation(dict_pref))

    print("\nYearly artist recommendation:")
    print(help.generate_yearly_song_recommendation(dict_pref))

    print("\nYearly artist recommendation:")
    print(help.generate_yearly_genre_recommendation(dict_pref))

    """
    
    def __init__(self,path):
        self.df_data = self.read_data(path)
        self.criterias = [
            'danceability', 'energy', 'loudness', 'speechiness',
            'acousticness', 'instrumentalness', 'liveness', 
            'valence', 'tempo', 'duration_ms'
        ]
        self.decade_genre_cache = pd.DataFrame()
        self.artist_decade_cache = pd.DataFrame()
        self.songs_decade_cache = pd.DataFrame()

    def read_data(self, path):
        df = pd.read_csv(path)
        numerical_columns = df.select_dtypes(include=['float64', 'int64'])
        #Normalisation par la moyenne
        for column in numerical_columns:
            col_mean = df[column].mean()
            col_range = df[column].max() - df[column].min()
            if col_range != 0:  # To avoid division by zero
                df[column] = (df[column] - col_mean) / col_range

        # scaler = MinMaxScaler()
        # normalized_data = scaler.fit_transform(numerical_columns)
        # df_normalized = pd.DataFrame(normalized_data, columns=numerical_columns.columns, index=df.index)
        # df.update(df_normalized)
        return df

 
    ## ------  Visualisation 1  -----------

    def generate_user_preferences_dict(self,dict_pref):
        criterias = ['danceability','energy','loudness','speechiness','acousticness','instrumentalness','liveness','valence','tempo','duration_ms']
        pref_values = {}
        df_filtered = self.df_data[self.df_data['track_artist'].isin(dict_pref['artistes']) & self.df_data['playlist_subgenre'].isin(dict_pref['sous_genres'])]
        for criteria in criterias:            
            pref_values[criteria] = df_filtered[criteria].mean()
        return pref_values


    def generate_average_preferences_dict(self):
        criterias = ['danceability','energy','loudness','speechiness','acousticness','instrumentalness','liveness','valence','tempo','duration_ms']
        mean_pref_values = {}
        for criteria in criterias:            
            mean_pref_values[criteria] = self.df_data[criteria].mean()
        return mean_pref_values

    ## ------  Visualisation 2  -----------

    def generate_subgenre_similarity_df(self,dict_pref):
        criterias = ['danceability','energy','loudness','speechiness','acousticness','instrumentalness','liveness','valence','tempo','duration_ms']
        df_subgenres = self.df_data.groupby(['playlist_genre','playlist_subgenre'])[criterias].mean().reset_index()
        user_pref_dict = self.generate_user_preferences_dict(dict_pref)
        user_pref_df = pd.DataFrame([user_pref_dict], columns=user_pref_dict.keys())
        df_subgenres['similarity'] = df_subgenres[criterias].apply(lambda x: 1 - distance.euclidean(x, user_pref_df.values.flatten()), axis=1)
        return df_subgenres[['playlist_genre','playlist_subgenre','similarity']]

    ## ------  Visualisation 3  -----------

    def generate_recommendations_df(self,dict_pref, recommendation_type='chansons'):
        """Fonction pour générer un dataframe avec les recommendations selon le type, 
        en plus du dictionnaire nécessaire pour le radar chart.

        Args:
            dict_pref (Dict): Un dictionnaire avec les préférences utilisateurs
            recommendation_type (str, optional): Choix du type de recommendations ('chansons','artistes' ou 'playlist'). 
                Defaults to 'chansons'.

        Returns:
            DataFrame: Dataframe avec la comparaison des chansons/artistes/playlist avec le score de similarité (0->1)
            Dict: dictionnaire qui contient les valeurs moyennes de la sélection
        """
        criterias = ['danceability','energy','loudness','speechiness','acousticness','instrumentalness','liveness','valence','tempo','duration_ms']
        if recommendation_type == 'chansons':
            df_compare = self.df_data.groupby(['track_artist','track_name','track_popularity'])[criterias].mean()
        elif recommendation_type == 'artistes':
            df_compare = self.df_data.groupby(['track_artist'])[criterias].mean()
        elif recommendation_type == 'playlist':
            df_compare = self.df_data.groupby(['playlist_name'])[criterias].mean()
        user_pref_dict = self.generate_user_preferences_dict(dict_pref)
        user_pref_df = pd.DataFrame([user_pref_dict], columns=user_pref_dict.keys())
        df_compare['similarity'] = df_compare[criterias].apply(lambda x: 1 - distance.euclidean(x, user_pref_df.values.flatten()), axis=1)
        df_compare = df_compare.sort_values(by='similarity',ascending=False).head(10)
        mean_pref_values = {}
        for criteria in criterias:            
            mean_pref_values[criteria] = df_compare[criteria].mean()
        return df_compare, mean_pref_values
    
    ## ------  Visualisation 4  -----------
    
    def generate_yearly_song_recommendation(self,dict_pref):
        """Fonction pour générer un dataframe avec les chansons les plus similaires au profil, 
        par année, sous forme de dataframe avec les caractéristiques.

        Args:
            dict_pref (Dict): Un dictionnaire avec les préférences utilisateurs

        Returns:
            DataFrame: Dataframe avec les chansons par année qui sont les plus proches du profil
        """
        if self.songs_decade_cache.empty == False:
            return self.songs_decade_cache
        
        criterias = ['danceability','energy','loudness','speechiness','acousticness','instrumentalness','liveness','valence','tempo','duration_ms']

        self.df_data['year'] = pd.to_datetime(self.df_data['track_album_release_date'], format='%Y-%m-%d').dt.year
        df_compare = self.df_data.groupby(['track_name','track_album_name','year','track_artist','track_popularity'])[criterias].mean()

        user_pref_dict = self.generate_user_preferences_dict(dict_pref)
        user_pref_df = pd.DataFrame([user_pref_dict], columns=user_pref_dict.keys())
        df_compare['similarity'] = df_compare[criterias].apply(lambda x: 1 - distance.euclidean(x, user_pref_df.values.flatten()), axis=1)
        df_compare = df_compare.reset_index()

        max_similarity_per_year = df_compare.groupby('year')['similarity'].max().reset_index()
        df_max_similarity = pd.merge(df_compare, max_similarity_per_year, on=['year', 'similarity'])
        df_max_similarity = df_max_similarity.drop_duplicates(subset=['year', 'similarity'])
        song_similarity = df_max_similarity.reset_index(drop=True)
        
        self.songs_decade_cache = song_similarity
        return song_similarity
    
    def generate_yearly_artist_recommendation(self,dict_pref):
        """Fonction pour générer un dataframe avec les artiste les plus similaires au profil, 
        par année, sous forme de dataframe avec les caractéristiques.

        Args:
            dict_pref (Dict): Un dictionnaire avec les préférences utilisateurs

        Returns:
            DataFrame: Dataframe avec les artistes par année qui sont les plus proches du profil
        """
        if self.artist_decade_cache.empty == False:
            return self.artist_decade_cache
        
        criterias = ['danceability','energy','loudness','speechiness','acousticness','instrumentalness','liveness','valence','tempo','duration_ms']

        self.df_data['year'] = pd.to_datetime(self.df_data['track_album_release_date'], format='%Y-%m-%d').dt.year
        df_compare = self.df_data.groupby(['year','track_artist'])[criterias].mean()

        user_pref_dict = self.generate_user_preferences_dict(dict_pref)
        user_pref_df = pd.DataFrame([user_pref_dict], columns=user_pref_dict.keys())
        df_compare['similarity'] = df_compare[criterias].apply(lambda x: 1 - distance.euclidean(x, user_pref_df.values.flatten()), axis=1)
        df_compare = df_compare.reset_index()

        max_similarity_per_year = df_compare.groupby('year')['similarity'].max().reset_index()
        df_max_similarity = pd.merge(df_compare, max_similarity_per_year, on=['year', 'similarity'])
        df_max_similarity = df_max_similarity.drop_duplicates(subset=['year', 'similarity'])
        artist_similarity = df_max_similarity.reset_index(drop=True)
        
        self.artist_cache = artist_similarity
        return artist_similarity
    
    def generate_yearly_genre_recommendation(self,dict_pref):
        """Fonction pour générer un dataframe avec les genres les plus similaires au profil, 
        par année, sous forme de dataframe avec les caractéristiques.

        Args:
            dict_pref (Dict): Un dictionnaire avec les préférences utilisateurs

        Returns:
            DataFrame: Dataframe avec les genres par année qui sont les plus proches du profil
        """
        if self.decade_genre_cache.empty == False:
            return self.decade_genre_cache
        
        criterias = ['danceability','energy','loudness','speechiness','acousticness','instrumentalness','liveness','valence','tempo','duration_ms']

        self.df_data['year'] = pd.to_datetime(self.df_data['track_album_release_date'], format='%Y-%m-%d').dt.year
        df_compare = self.df_data.groupby(['year','playlist_genre'])[criterias].mean()

        user_pref_dict = self.generate_user_preferences_dict(dict_pref)
        user_pref_df = pd.DataFrame([user_pref_dict], columns=user_pref_dict.keys())
        df_compare['similarity'] = df_compare[criterias].apply(lambda x: 1 - distance.euclidean(x, user_pref_df.values.flatten()), axis=1)
        df_compare = df_compare.reset_index()

        max_similarity_per_year = df_compare.groupby('year')['similarity'].max().reset_index()
        df_max_similarity = pd.merge(df_compare, max_similarity_per_year, on=['year', 'similarity'])
        df_max_similarity = df_max_similarity.drop_duplicates(subset=['year', 'similarity'])
        genre_similarity = df_max_similarity.reset_index(drop=True)
        
        self.decade_genre_cache = genre_similarity
        return genre_similarity
# %%
