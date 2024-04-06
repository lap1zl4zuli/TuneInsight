import os
import spotipy
import webbrowser
import pandas as pd
from tqdm import tqdm
from IPython.display import clear_output
from dateutil.parser import parse
from urllib.parse import urlparse
from spotipy.oauth2 import SpotifyOAuth
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer
from sklearn.preprocessing import StandardScaler, MinMaxScaler, MaxAbsScaler, RobustScaler, QuantileTransformer, Normalizer

class RedirectHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handles GET requests in the HTTP server.

        Returns
        -------
        None

        Examples
        --------
        >>>
        """

        query_components = parse_qs(urlparse(self.path).query)

        authorization_code = query_components.get('code', [None])[0]

        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

        self.wfile.write(b'Authorization successful. You can close this window now.')

        self.server.authorization_code = authorization_code

class TuneInsight:
    """
    TuneInsight class provides methods to analyze Spotify playlists and extract audio features of tracks.

    Attributes:
        client_id (str): Client ID for accessing Spotify API.
        client_secret (str): Client secret for accessing Spotify API.
        redirect_uri (str): Redirect URI for authentication.
        token (str): Access token for Spotify API authentication.
        scalers (list): List of scaler objects for feature scaling.
    """

    def __init__(self):
        """Initialize TuneInsight.

        Initializes TuneInsight with necessary attributes and obtains access token.

        Returns
        -------
        None

        Examples
        --------
        >>>
        """
        self.client_id = 'CLIENT_ID'
        self.client_secret = 'CLIENT_SECRET'
        self.redirect_uri = "http://localhost:8888/callback"
        self.token = None
        self.scalers = [
            StandardScaler(), MinMaxScaler(), MaxAbsScaler(),
            RobustScaler(), QuantileTransformer(), Normalizer()
        ]
        self.sp = None  

        os.chdir("../")
        self.project_dir = os.getcwd()
        self.spreadsheets_dir = os.path.join(self.project_dir, "Spreadsheets")
        if not os.path.exists(self.spreadsheets_dir):
            os.makedirs(self.spreadsheets_dir)

        sp_oauth = SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=[
                "user-follow-read", "user-follow-modify", "user-library-read",
                "user-top-read", "playlist-read-private", "playlist-read-collaborative"
            ]
        )

        auth_url = sp_oauth.get_authorize_url()

        server_address = ('', 8888)
        httpd = HTTPServer(server_address, RedirectHandler)

        try:

            webbrowser.open(auth_url)

            httpd.handle_request()

            authorization_code = httpd.authorization_code

            token_info = sp_oauth.get_access_token(authorization_code)

            self.token = token_info['access_token']

            if self.token:
                print("Authentication successful.")
                self.sp = spotipy.Spotify(auth=self.token)
            else:
                print("Failed to authenticate. Please check your credentials and try again.")

        except Exception as e:
            print("Error during authentication:", e)

        finally:
            httpd.server_close()

    def get_user_playlists(self, scale=False, username=False, to_csv=False, dropna=True, parse_date=True):
        """Retrieve audio features of tracks in a user's playlists.

        Parameters
        ----------
        scale : bool, default=False
            Whether to scale the audio features.
        username : bool, default=False
            Whether to prompt for a username.
        to_csv : bool, default=False
            Whether to save the DataFrame to a CSV file.
        dropna : bool, default=True
            Whether to drop null values.
        parse_date : bool, default=True
            Whether to parse dates.

        Returns
        -------
        DataFrame
            DataFrame containing audio features of tracks in the playlist.

        Examples
        --------
        >>> spa.get_user_playlists(scale=True, to_csv=True)
        """
        if username:
            username = urlparse(input("Enter Spotify Profile URL")).path.split('/')[2]
            user_playlists = self.sp.user_playlists(username)
        else:    
            user_playlists = self.sp.current_user_playlists()
            

        dfs = []

        for i, playlist in enumerate(user_playlists['items']):
            print(f"{i}. {playlist['name']}")
        print(f'{len(user_playlists['items'])}. All')

        selected_playlist_index = int(input("Enter the number of the playlist you want to retrieve songs from: "))

        clear_output(wait=True)
        if 0 <= selected_playlist_index < len(user_playlists['items']):
            selected_playlist_id = user_playlists['items'][selected_playlist_index]['id']
            try:
                return self.playlist_df(playlist_id=selected_playlist_id, scale=scale, to_csv=to_csv, dropna=dropna, parse_date=parse_date)
            except Exception as e:
                print(e)
                print("-------------------------------")
                print("This playlist can't be retrieved")

        elif selected_playlist_index == len(user_playlists['items']):
            for i in user_playlists['items']:
                id = i['id']
                dfs.append(self.playlist_df(playlist_id=id, scale=scale, to_csv=False, dropna=dropna, parse_date=parse_date))

            df_main = pd.concat(dfs,ignore_index=True)
            df_main.drop_duplicates(subset=['songs'],inplace=True)
            df_main.to_csv(os.path.join(self.spreadsheets_dir, "playlist_df.csv"),index=False)
            self.playlistdf = df_main
            return df_main
        else:
            print("Invalid playlist number. Please choose a valid playlist.")


    def get_top_tracks(self, scale=False, dropna=True, to_csv=False, parse_date=True):
        """Retrieve audio features of a user's top tracks.

            Parameters
            ----------
            scale : bool, default=False
                Whether to scale the audio features.
            dropna : bool, default=True
                Whether to drop null values.
            to_csv : bool, default=False
                Whether to save the DataFrame to a CSV file.
            parse_date : bool, default=True
                Whether to parse dates.

            Returns
            -------
            DataFrame
                DataFrame of user's top tracks data.

            Examples
            --------
            >>> spa.get_top_tracks(scale=True, to_csv=True)
            """
        top_tracks = []
        offset = 0
        limit = 50  # Maximum number of top_tracks per request

        while True:
            results = self.sp.current_user_top_tracks(offset=offset, limit=limit)
            top_tracks.extend(results['items'])
            offset += limit

            if results['next'] is None:
                break  # No more top_tracks available

        track_ids = [track['id'] for track in top_tracks]

        batch_size = 50
        batches = [track_ids[i:i + batch_size] for i in range(0, len(track_ids), batch_size)]

        name = [track['name'] for track in top_tracks]
        artist = [track['artists'][0]['name'] for track in top_tracks]

        artist_ids = [track['artists'][0]['id'] for track in top_tracks]
        track_genres = []

        for track in tqdm(top_tracks, desc="Fetching Track Genres"):
            artists = [artist['name'] for artist in track['artists']]
            artist_genres = []

            for artist in artists:
                artist_info = self.sp.search(q='artist:' + artist, type='artist')
                if artist_info['artists']['items']:
                    genres = artist_info['artists']['items'][0]['genres']
                    artist_genres.extend(genres)

            if artist_genres:
                track_genres.append(artist_genres[0])
            else:
                track_genres.append(None)


        album = [track['album']['name'] for track in top_tracks]
        release_date = [track['album']['release_date'] for track in top_tracks]
        is_local = [track['is_local'] for track in top_tracks]
        explicit = [track['explicit'] for track in top_tracks]
        popularity = [track['popularity'] for track in top_tracks]
        duration_min = [track['duration_ms']/60000 for track in top_tracks]

        track_features = []
        for batch in tqdm(batches, desc="Retrieving Audio Features"):
            batch_features = self.sp.audio_features(batch)
            track_features.extend(batch_features)

        audio_features = ['danceability', 'energy', 'key', 'loudness', 'mode', 
                          'speechiness', 'acousticness', 'instrumentalness',
                          'liveness', 'valence', 'tempo']

        danceability = []
        energy = []
        key = []
        loudness = []
        mode = []
        speechiness = []
        acousticness = []
        instrumentalness = []
        liveness = []
        valence = []
        tempo = []

        for data in tqdm(track_features, desc="Extracting Audio Features"):
            if data:
                danceability.append(data['danceability'])
                energy.append(data['energy'])
                key.append(data['key'])
                loudness.append(data['loudness'])
                mode.append(data['mode'])
                speechiness.append(data['speechiness'])
                acousticness.append(data['acousticness'])
                instrumentalness.append(data['instrumentalness'])
                liveness.append(data['liveness'])
                valence.append(data['valence'])
                tempo.append(data['tempo'])
            else:
                # Fill with NaN if data is None
                danceability.append(float('nan'))
                energy.append(float('nan'))
                key.append(float('nan'))
                loudness.append(float('nan'))
                mode.append(float('nan'))
                speechiness.append(float('nan'))
                acousticness.append(float('nan'))
                instrumentalness.append(float('nan'))
                liveness.append(float('nan'))
                valence.append(float('nan'))
                tempo.append(float('nan'))

        dic = {'songs': name,
            'genre': track_genres,
            'artist': artist,
            'album': album,
            'release_date': release_date,
            'is_local': is_local,
            'explicit': explicit,
            'popularity': popularity,
            'duration_min': duration_min,
            'danceability': danceability,
            'energy': energy,
            'key': key,
            'loudness': loudness,
            'mode': mode,
            'speechiness': speechiness,
            'acousticness': acousticness,
            'instrumentalness': instrumentalness,
            'liveness': liveness,
            'valence': valence,
            'tempo': tempo}

        df = pd.DataFrame.from_dict(dic)
        if dropna:
            df.dropna(inplace=True)
            df = df[df['release_date']!='0000']
            df.reset_index(inplace=True, drop=True)
        if parse_date:
            for i in tqdm(range(len(df)), desc="Parsing Dates"):
                df.loc[i,'release_date']  = parse(df.loc[i,'release_date']).date()
        if scale:
            return self.__scale_audio_features(df, audio_features, to_csv, top_tracks=True)
        else:
            df.to_csv(os.path.join(self.spreadsheets_dir, "top_tracks_df.csv"),index=False)
            self.toptracks_df = df
            return df
    def get_user_episodes(self, to_csv=False):
        """Retrieve episodes saved by the current user from Spotify.

        Parameters
        ----------
        to_csv : bool, default=False
            Whether to save the DataFrame to a CSV file.

        Returns
        -------
        DataFrame
            DataFrame containing information about saved episodes.

        Examples
        --------
        >>> spa.get_user_episodes(to_csv=True)
        """
        eps = self.sp.current_user_saved_episodes()
        ids = [episode['episode']['id'] for episode in eps['items']]
        names = [episode['episode']['name'] for episode in eps['items']]
        durations = [episode['episode']['duration_ms'] / 60000 for episode in eps['items']]
        languages = [episode['episode']['language'] for episode in eps['items']]
        dates = [episode['episode']['release_date'] for episode in eps['items']]
        show_names = [episode['episode']['show']['name'] for episode in eps['items']]
        publishers = [episode['episode']['show']['publisher'] for episode in eps['items']]
        explicits = [episode['episode']['explicit'] for episode in eps['items']]

        eps_df = pd.DataFrame({
            "name": names,
            "duration_min": durations,
            "language": languages,
            "release_date": dates,
            "show": show_names,
            "publisher": publishers,
            "explicit": explicits}
        )

        if to_csv:
            eps_df.to_csv(os.path.join(self.spreadsheets_dir, "saved_episodes.csv"),index=False)
        
        self.epsdf = eps_df
        return eps_df

    def __scale_audio_features(self, df, cols_to_scale, to_csv=False, top_tracks=False):
        """Scale the specified columns of the DataFrame.

        Parameters
        ----------
        df : DataFrame
            DataFrame containing the columns to be scaled.
        cols_to_scale : list
            List of column names to be scaled.
        to_csv : bool, default=False
            Whether to save the DataFrame to a CSV file.
        top_tracks : bool, default=False
            Whether the DataFrame is for top tracks.

        Returns
        -------
        DataFrame
            DataFrame with scaled columns.
        """
        for col in tqdm(cols_to_scale, desc="Scaling Audio Features"):
            df[col] = pd.DataFrame(self.scalers[0].fit_transform(pd.DataFrame(df[col])), columns=[col])
        clear_output()

        if to_csv:
            if top_tracks:
                df.to_csv(os.path.join(self.spreadsheets_dir, "top_tracks_df.csv"),index = False)
                self.toptracks_df = df
            else:
                df.to_csv(os.path.join(self.spreadsheets_dir, "playlist_df.csv"),index = False)
                self.playlistdf = df
        return df

    def playlist_df(self, playlist_id=None, url=None, scale=False, dropna=True, to_csv=False, parse_date = True):
        """Retrieve audio features of tracks in a playlist.

        Parameters
        ----------
        playlist_id : str, optional
            Playlist ID.
        url : str, optional
            URL of the playlist.
        scale : bool, default=False
            Whether to scale the audio features.
        dropna : bool, default=True
            Whether to drop null values.
        to_csv : bool, default=False
            Whether to save the DataFrame to a CSV file.
        parse_date : bool, default=True
            Whether to parse dates.

        Returns
        -------
        DataFrame
            DataFrame containing audio features of tracks in the playlist.

        Examples
        --------
        >>> spa.playlist_df(playlist_id='your_playlist_id', scale=True, to_csv=True)
        """
        if url:
            playlist_id = urlparse(url).path.split('/')[2]

        try:
            playlist_info = self.sp.playlist(playlist_id)
            playlist_name = playlist_info['name']
            data = []
            offset = 0
            limit = 100 

            while True:
                results = self.sp.playlist_tracks(playlist_id, offset=offset, limit=limit)
                data.extend(results['items'])
                offset += limit

                if results['next'] is None:
                    break

        except Exception as e:
            print(f"Error retrieving playlist data: {e}")
            print("-------------------------------")
            print("This playlist can't be retrieved")
            return None

        songs = [track["track"]['name'] for track in tqdm(data, desc='Retrieving track names...')]
        self.track_names = songs
        clear_output(wait=True)

        track_artists_ids = [track['track']['artists'][0]['id'] for track in tqdm(data, desc='Retrieving track artists ids...')]
        self.track_artists_ids = track_artists_ids
        clear_output(wait=True)

        track_genres = []

        for track in tqdm(data, desc="Retrieving Track Genres"):
            artists = [artist['name'] for artist in track['track']['artists']]
            artist_genres = []

            for artist in artists:
                artist_info = self.sp.search(q='artist:' + artist, type='artist')
                if artist_info['artists']['items']:
                    genres = artist_info['artists']['items'][0]['genres']
                    artist_genres.extend(genres)
            if artist_genres:
                track_genres.append(artist_genres[0])
            else:
                track_genres.append(None)
        clear_output(wait=True)

        track_locality = [track['is_local'] for track in tqdm(data, desc='Retrieving track locality...')]
        clear_output(wait=True)

        track_ids = [track['track']['id'] for track in tqdm(data, desc='Retrieving track ids...')]
        clear_output(wait=True)

        track_artists = [track['track']['artists'][0]['name'] for track in tqdm(data, desc='Retrieving track artists...')]
        clear_output(wait=True)
        self.track_artists = track_artists

        track_album = [track['track']['album']['name'] for track in tqdm(data, desc='Retrieving track album...')]
        clear_output(wait=True)

        track_date = [track['track']['album']['release_date'] for track in tqdm(data, desc='Retrieving track date...')]
        clear_output(wait=True)

        tracks_popularity = [track['track']['popularity'] for track in tqdm(data, desc='Retrieving track popularity...')]
        clear_output(wait=True)

        tracks_duration = [track['track']['duration_ms']/60000 for track in tqdm(data, desc='Retrieving track duration...')]
        clear_output(wait=True)

        track_explicit = [track['track']['explicit'] for track in tqdm(data, desc='Retrieving track explicity...')]
        clear_output(wait=True)



        batch_size = 50
        batches = [track_ids[i:i + batch_size] for i in range(0, len(track_ids), batch_size)]

        song_data = []
        for batch in tqdm(batches, desc="Retrieving audio features"):
            batch_features = self.sp.audio_features(batch)
            song_data.extend(batch_features)

        clear_output(wait=True)

        audio_features = ['danceability', 'energy', 'key', 'loudness', 'mode',
                        'speechiness', 'acousticness', 'instrumentalness',
                        'liveness', 'valence', 'tempo']

        danceability = []
        energy = []
        key = []
        loudness = []
        mode = []
        speechiness = []
        acousticness = []
        instrumentalness = []
        liveness = []
        valence = []
        tempo = []

        for data in tqdm(song_data, desc="Extracting Audio Features"):
            if data:
                danceability.append(data['danceability'])
                energy.append(data['energy'])
                key.append(data['key'])
                loudness.append(data['loudness'])
                mode.append(data['mode'])
                speechiness.append(data['speechiness'])
                acousticness.append(data['acousticness'])
                instrumentalness.append(data['instrumentalness'])
                liveness.append(data['liveness'])
                valence.append(data['valence'])
                tempo.append(data['tempo'])
            else:
                # Fill with NaN if data is None
                danceability.append(float('nan'))
                energy.append(float('nan'))
                key.append(float('nan'))
                loudness.append(float('nan'))
                mode.append(float('nan'))
                speechiness.append(float('nan'))
                acousticness.append(float('nan'))
                instrumentalness.append(float('nan'))
                liveness.append(float('nan'))
                valence.append(float('nan'))
                tempo.append(float('nan'))

        dic = { 'songs': songs,
                'playlist' : [playlist_name]*len(songs),
                'genre': track_genres,
                'artist': track_artists,
                'album': track_album,
                'release_date': track_date,
                'is_local': track_locality,
                'explicit': track_explicit,
                'popularity': tracks_popularity,
                'duration_min': tracks_duration,
                'danceability': danceability,
                'energy': energy,
                'key': key,
                'loudness': loudness,
                'mode': mode,
                'speechiness': speechiness,
                'acousticness': acousticness,
                'instrumentalness': instrumentalness,
                'liveness': liveness,
                'valence': valence,
                'tempo': tempo}

        df = pd.DataFrame.from_dict(dic)
        if dropna:
            df.dropna(inplace=True)
            df = df[df['release_date']!='0000']
            df.reset_index(inplace=True, drop=True)
        if parse_date:
            for i in tqdm(range(len(df)), desc="Parsing Date"):
                df.loc[i,'release_date']  = parse(df.loc[i,'release_date']).date()
            clear_output()
        if scale:
            return self.__scale_audio_features(df, audio_features, to_csv)
        else:
            df.to_csv(os.path.join(self.spreadsheets_dir, "playlist_df.csv"),index=False)
            self.playlistdf = df
            return df
