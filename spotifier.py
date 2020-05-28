import youtube_dl
import requests 
import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

from __future__ import unicode_literals
from secrets import spotifyToken, spotifyUserId

class CreatePlaylist:
    
    def __init__(self):
        self.youtubeClient = self.getYoutubeClient()
        self.allSongInfo = {}

    def getYoutubeClient(self):
        
        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "client_secret.json"

        # Get credentials and create an API client
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        credentials = flow.run_console()
        youtubeClient = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)


        return youtubeClient

    
    def getPlaylist(self):
        #Grab a youtube PLAYLIST 
        playlistList = []


        request = self.youtubeClient.playlists().list(
            part="snippet,status,id",
            mine=True
        )
        response = request.execute()

        for key, item in enumerate(response["items"],start=1):
            playlistId = item["id"]
            playlistTitle = item["title"]
            playlistList.append([playlistId,playlistTitle])

            print(f"{key} - {playlistTitle}")

        playNum = int(input(f"Select the number of the desired playlist [1 to {key}]: "))
        #Since python positions are 0-based...
        playPos = playNum - 1

        return playlistList[playPos]

    def getPlaylistItems(self):

        #lets retrieve the videos information from the selected playlist
        playlist = self.getPlaylist() 
        #Remember that "playlist" is just a list containg 2 items, playlistId and playlistTitle  
        playlistID = self.playlist[0]

        request = self.youtubeClient.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=f"{playlistID}"
        )

        response = request.execute()

        for key, item in enumerate(response["items"]):
            videoId = item["contentDetails"]["videoId"]
            videoTitle = item["snippet"]["title"]
            

            youtubeUrl = f"https://www.youtube.com/watch?v={videoId}"

            video = youtube_dl.Youtube({}).extract_info(
                youtubeUrl, download=False
            )

            songName = video["track"]
            artist = video["artist"]


            if songName is not None and artist is not None:
                # save all important info and skip any missing song and artist

                self.allSongInfo[videoTitle] = {
                    "youtubeUrl": youtubeUrl,
                    "songName": songName,
                    "artist": artist,

                    # add the uri, easy to get song to put into playlist
                    "spotify_uri": self.getSpotifyUri(songName, artist)
                }


        
    def createPlaylist(self):
        
        request_body = json.dumps({
            "name": f'{youtubePlaylist}",
            "description": f"This is my {youtubePlaylist}",
            "public": True,

        })

        query = f"https://api.spotify.com/v1/users/{}/playlists"
        response = requests.post(
            query,
            data=request_body,
            headers={
                "Content-Type":"application/json",
                "Authorization": f"Bearer {spotifyToken}"

            }
        )

        response_json = response.json()

        return response_json["id"]

    def getSpotifyUri(self, songName, artist):
        query = f"https://api.spotify.com/v1/search?query=track%3A{songName}+artist%3A{artist}&type=track&offset=0&limit=20"

        response = requests.get(
            query,
            headers={
                "Content-Type": "application",
                "Authorization": f"Bearer {spotifyToken}"
            }
        )

        response_json = response.json()
        songs = respose_json["tracks"]["items"]

        uri = songs[0]["uri"]

        return uri

    def addSongToPlaylist(self):
        pass


#Se não a música não existe no spotify, vamos baixar ela
ydl_opts = {}
with youtube_dl.YoutubeDL(ydl_opts) as ydl:
    ydl.download(['https://www.youtube.com/watch?v=BaW_jenozKc'])


if __name__ == "__main__":
    main()