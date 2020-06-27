import json
import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import requests
import youtube_dl

from secrets import spotify_user_id, spotify_token

"""
Step 1: Log into Youtube
Step 2: Grab our liked videos
Step 3: Create a new Playlist
Step 4: Search for the Song
Step 5: Add the song into the new Spotify Playlist
"""

class CreatePlaylist:

    def __init__(self):
        self.youtube_client = self.get_youtube_client()
        self.all_song_info = {}

    # Step 1: Log into Youtube
    def get_youtube_client(self):
        # Copied from Youtube Data API
        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "client_secrets.json"

        # Get credentials and create an API client
        scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
        credentials = flow.run_console()
       
       # from the Youtube DATA Api
        youtube_client = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)

        return youtube_client

    # Step 2: Grab our liked videos
    def get_liked_videos(self):
        request = self.youtube_client.videos().list(
            part="snippet, contentDetails, statistics",
            myRating="like"
        )

        response = request.execute()
        
        # collect each video and get important information
        for item in response["items"]:
            video_title = item["snippet"]["title"]
            youtube_url = "https://www.youtube.com/watch?v={}".format(item["id"])

            # use youtube_dl to collect the song name and artist name
            video = youtube_dl.YoutubeDL({}).extract_info(youtube_url, download=False)
            song_name = video["track"]
            artist = video["artist"]

            # save all important info
            self.all_song_info[video_title]={
                "youtube_url" : youtube_url,
                "song_name" : song_name,
                "artist" : artist,

                #add the uri, easy to get the song to put in the playlist
                "spotify_uri":self.get_spotify_uri(song_name, artist)
            
            }

    # Step 3: Create a new Playlist
    def create_playlist(self):
        request_body = json.dumps({
            "name":"Youtube Liked Videos",
            "description": "All liked Youtube Videos",
            "public": True,
        })

        query = "https://api.spotify.com/v1/users/{}/playlists".format(spotify_user_id)
        response = requests.post(
            query,
            data=request_body,
            headers={
                "Content-Type":"application/json",
                "Authorization":"Bearer {}".format(spotify_token)
            }
        )

        response_json = response.json()

        return response_json["id"]
        

    # Step 4: Search for the Song
    def get_spotify_uri(self, song_name, artist):
        
        query = "https://api.spotify.com/v1/search?query=track3A{}&+artist%3A{}&type=track&offset=0&limit=20".format(song_name , artist)
        response = requests.get(
            query,
            headers={
                "Content-Type": "application/json",
                "Authorization" : "Bearer {}".format(spotify_token)
            }
        )

        response_json = response.json
        songs = response_json["tracks"]["items"]

        #only use the first song
        uri = songs[0]["uri"]

        return uri

    # Step 5: Add the song into the new Spotify Playlist
    def add_song_to_playlist(self):
        #populate our songs disctionary
        
        self.get_liked_videos()

        #collect all of uri
        uris = [info["spotify_uri"]
            for song , info in self.all_song_info.items()]

        #create a playlist
        playlist_id = self.create_playlist()

        #add all songs into new playlist
        request_data = json.dumps(uris)

        query = "https://api.spotify.com/v1/playlists/{}/tracks".format(playlist_id)

        response = requests.post(
            query,
            data = request_data,
            headers= {
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotify_token)
            }
        )
        response_json = response.json()
        return response_json