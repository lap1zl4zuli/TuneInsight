# Spotify Playlist Analyzer

The Spotify Playlist Analyzer is a Python application that allows users to analyze Spotify playlists, extract audio features of tracks, and perform various operations such as retrieving user playlists, top tracks, and saved episodes. It utilizes the Spotify API to access user data and retrieve information about playlists, tracks, and episodes.

## Features

- Retrieve user playlists from Spotify.
- Analyze audio features of tracks in playlists.
- Retrieve top tracks of the user.
- Retrieve saved episodes from the user's Spotify account.
- Scale audio features using various scalers.
- Save data to CSV files for further analysis.

## Installation

To use the Spotify Playlist Analyzer, follow these steps:

1. Clone the repository to your local machine:

   ```bash
   git clone https://github.com/your-username/spotify-playlist-analyzer.git
   ```
2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:

   ```bash
   from SpotifyPlaylistAnalyzer import SpotifyPlaylistAnalyzer
   spa = SpotifyPlaylistAnalyzer()
   ```

## Usage

Here are some examples of how to use the Spotify Playlist Analyzer:

```python
from SpotifyPlaylistAnalyzer import SpotifyPlaylistAnalyzer

# Initialize the analyzer
spa = SpotifyPlaylistAnalyzer()

# Retrieve user playlists and save to CSV
playlist_df = spa.get_user_playlists(to_csv=True)
display(playlist_df.head())

# Retrieve saved episodes and save to CSV
saved_episodes = spa.get_user_episodes(to_csv=True)
display(saved_episodes.head()

# Retrieve top tracks, scale audio features, and save to CSV
top_tracks = spa.get_top_tracks(to_csv=True, scale=True)
display(top_tracks.head())
```

# Security Notice

Please ensure that you do not expose your Spotify API client ID and client secret publicly. Store them securely and avoid hardcoding them directly into your codebase.

# License

This project is licensed under the MIT License. See the [LICENSE ](LICENSE)file for details.
