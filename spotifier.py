from __future__ import unicode_literals
import json
import requests 
import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import youtube_dl

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
        scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        credentials = flow.run_console()
        youtubeClient = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)


        return youtubeClient

    
    def getPlaylistItems(self):
        #Grab a youtube PLAYLIST first
        playlistList = []


        request = self.youtubeClient.playlists().list(
            part="snippet,status,id",
            mine=True
        )
        response = request.execute()

        for key, items in enumerate(response["items"],start=1):
            playlistId = items["id"]
            playlistTitle = items["snippet"]["title"]
            playlistList.append([playlistId,playlistTitle])

            print(f"{key} - {playlistTitle}")

        playNum = int(input(f"Select the number of the desired playlist [1 to {key}]: "))
        #Since python positions are 0-based...
        playPos = playNum - 1

        playlist = playlistList[playPos]

        #Remember that "playlist" is just a list containg 2 items, playlistId and playlistTitle  
        playlistID = playlist[0]
        playlistName = playlist[1]
        #nextPageToken
        request = self.youtubeClient.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=f"{playlistID}",
            maxResults=20
        )

        response = request.execute()

        for key, item in enumerate(response["items"]):
            videoId = item["contentDetails"]["videoId"]
            videoTitle = item["snippet"]["title"]
            

            youtubeUrl = f"https://www.youtube.com/watch?v={videoId}"

            video = youtube_dl.YoutubeDL({}).extract_info(
                youtubeUrl, download=False
            )

            print(key+1)
            songName = video["track"]
            artist = video["artist"]

            print(f"{key} - This is the songName: {songName} This is the artist: {artist}")

            if songName is not None and artist is not None:
                # save all important info and skip any missing song and artist

                self.allSongInfo[videoTitle] = {
                    "youtubeUrl": youtubeUrl,
                    "songName": songName,
                    "artist": artist,

                    # add the uri, easy to get song to put into playlist
                    "spotify_uri": self.getSpotifyUri(songName, artist,)
                }
            

        return playlistName

        
    def createPlaylist(self,playlistName):
        
        request_body = json.dumps({
            "name": f"{playlistName}",
            "description": f"This is my {playlistName} Playlist from Youtube",
            "public": True,

        })

        query = f"https://api.spotify.com/v1/users/{spotifyUserId}/playlists"
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
        query = f"https://api.spotify.com/v1/search?q=track%3A{songName}%20artist%3A{artist}&type=track&offset=0&limit=20"

        response = requests.get(
            query,
            headers={
                "Content-Type": "application",
                "Authorization": f"Bearer {spotifyToken}"
            }
        )

        responseJson = response.json()
        songs = responseJson["tracks"]["items"]

        uri = songs[0]["uri"]

        return uri

    def addSongToPlaylist(self):
        #Populate dictionary
        playlistName = self.getPlaylistItems()

        #Collect all of Uris
        uris = [info["spotify_uri"]
            for song,info in self.allSongInfo.items()]

        #Create a new playlist
        playlistId = self.createPlaylist(playlistName)

        #add all songs into new playlist
        requestData = json.dumps(uris)
        print(requestData)

        query = f"https://api.spotify.com/v1/playlists/{playlistId}/tracks"

        response = requests.post(
            query,
            data=requestData,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {spotifyToken}"
            }
        )


        responseJson = response.json()
        return responseJson


    #Se não a música não existe no spotify, vamos baixar ela
    def DownloadToSpotify(self):
        pass

if __name__ == "__main__":
    cp = CreatePlaylist()
    cp.addSongToPlaylist()