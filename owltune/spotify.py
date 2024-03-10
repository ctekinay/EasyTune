import requests
import urllib.parse
#from datetime import datetime

class SpotifyAPI:
    def __init__(self, auth_url, token_url, client_id, client_secret, redirect_uri, api_base_url):
        self.auth_url = auth_url
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.api_base_url = api_base_url

    def get_auth_url(self, scope):
        """Generates the authorization URL for Spotify OAuth."""
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'scope': scope,
            'redirect_uri': self.redirect_uri,
            'show_dialog': True
        }
        return f"{self.auth_url}?{urllib.parse.urlencode(params)}"

    def exchange_code(self, code):
        """Exchanges the authorization code for an access token."""
        req_body = {
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        return requests.post(self.token_url, data=req_body)

    def refresh_access_token(self, refresh_token):
        """Refreshes the access token using a refresh token."""
        req_body = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        return requests.post(self.token_url, data=req_body)

    def get_user_playlists(self, access_token):
        """Retrieves the user's playlists using the access token."""
        headers = {'Authorization': f'Bearer {access_token}'}
        return requests.get(f"{self.api_base_url}me/playlists", headers=headers)

    def create_playlist(self, access_token, user_id, name, public, description=None):
        """Creates a new Spotify playlist for a user with error handling."""
        url = f"{self.api_base_url}users/{user_id}/playlists"
        headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
        payload = {'name': name, 'public': public, 'description': description}
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return None

    def add_tracks_to_playlist(self, access_token, playlist_id, track_uris):
        """Adds tracks to a Spotify playlist with error handling."""
        url = f"{self.api_base_url}playlists/{playlist_id}/tracks"
        headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
        payload = {'uris': track_uris}
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return None

    def get_user_id(self, access_token):
        """Fetch the Spotify user ID."""
        url = f"{self.api_base_url}me"
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get(url, headers=headers)
        return response.json().get('id')

    def search_track(self, access_token, song_name, artist_name=None):
        """Search for a track on Spotify."""
        query = urllib.parse.quote(song_name + ' ' + artist_name if artist_name else song_name)
        url = f"{self.api_base_url}search?q={query}&type=track"
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(url, headers=headers)
        results = response.json().get('tracks', {}).get('items', [])
        if results:
            # Assuming the first result is the correct one
            return results[0]['uri']
        return None

    def get_user_profile(self, access_token):
        """Fetch the Spotify user's profile."""
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(f"{self.api_base_url}me", headers=headers)
        return response.json()

    def unfollow_playlist(self, access_token, playlist_id):
        """Unfollows a Spotify playlist."""
        url = f"{self.api_base_url}playlists/{playlist_id}/followers"
        headers = {'Authorization': f'Bearer {access_token}'}
        try:
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
            return True, None  # Success, No error
        except requests.exceptions.RequestException as e:
            return False, str(e)  # Failure, Error message

    #Entering the songs realm
    def get_playlist_details(self, access_token, playlist_id):
        headers = {'Authorization': f'Bearer {access_token}'}
        url = f"{self.api_base_url}playlists/{playlist_id}"
        response = requests.get(url, headers=headers)
        return response

    def get_playlist_songs(self, access_token, playlist_id):
        url = f"{self.api_base_url}playlists/{playlist_id}/tracks"
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(url, headers=headers)
        return response

    def get_playlist_cover_image(self, access_token, playlist_id):
        url = f"https://api.spotify.com/v1/playlists/{playlist_id}/images"
        headers = {'Authorization': f'Bearer {access_token}'}
        return requests.get(url, headers=headers)