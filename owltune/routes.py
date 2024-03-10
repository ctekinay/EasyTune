import re
from . import app, spotify
from flask import redirect, request, jsonify, session, render_template, flash
from datetime import datetime
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)

# Welcome route
@app.route('/')
def index():
     # Render the 'welcome.html' template
    return render_template('welcome.html')

# Login route to initiate Spotify OAuth
@app.route('/login/')
def login():
    scope = 'user-read-private user-read-email playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public'
    auth_url = spotify.get_auth_url(scope)
    return redirect(auth_url)

# Callback route for handling OAuth response from Spotify
@app.route('/callback/')
def callback():
    error = request.args.get('error')
    code = request.args.get('code')

    if error:
        return jsonify({"error": error})

    if code:
        response = spotify.exchange_code(code)
        if response.status_code != 200:
            return jsonify({"error": "Failed to retrieve access token", "details": response.json()})

        token_info = response.json()
        session['access_token'] = token_info['access_token']
        session['refresh_token'] = token_info['refresh_token']
        session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']

        user_profile = spotify.get_user_profile(session['access_token'])  # This method should be defined in spotify.py
        session['username'] = user_profile['display_name']  # Store the username in session

        return redirect('/playlists')
    return jsonify({"error": "No code provided"})

# Route to display user's playlists
@app.route('/playlists')
def get_playlists():
    # Debugging: Print the current session to check its content
    print("Current session data:", session)

    # Check if the user is logged in
    if 'access_token' not in session or 'username' not in session:
    #    flash('You are not logged in. Please log in to view your playlists.')
        print("Redirecting to login - access token or username not in session")
        return redirect('/login')

    # Check if the access token has expired
    if datetime.now().timestamp() > session.get('expires_at', 0):
        #flash('Your session has expired. Please log in again.')
        print("Redirecting to refresh-token - access token expired")
        return redirect('/refresh-token')

    # Assuming you have some data representing playlist visibility, you can define it here:
    playlist_visibility = {
        'playlist_id_1': True,  # Replace with actual playlist IDs and visibility
        'playlist_id_2': False,
        # Add more entries as needed
    }

    response = spotify.get_user_playlists(session['access_token'])
    if response.status_code != 200:
        # Log the error details for debugging
        app.logger.error(f"Failed to retrieve playlists: {response.json()}")

        # Provide a user-friendly error message
        flash('Failed to retrieve playlists. Please try again later.')

        # Redirect to a different page or render an error page
        return redirect('/')

    playlists_json = response.json()

    # Debug to understand the playlist type: 'public' or 'private' - DISABLE LATER
    print("Playlists JSON:", playlists_json)  # Add this line to print the JSON data

    playlists_items = playlists_json.get('items', [])

    # Get the username from the session
    username = session.get('username', 'Guest')  # Use the username from the session, or 'Guest' if not found
    return render_template('playlists.html', playlists=playlists_items, username=username, access_token=session.get('access_token'), playlist_visibility=playlist_visibility)

# Route to refresh the access token
@app.route('/refresh-token')
def refresh_token():
    if 'refresh_token' not in session:
        return redirect('/login')

    response = spotify.refresh_access_token(session['refresh_token'])
    if response.status_code != 200:
        return jsonify({"error": "Failed to refresh access token", "details": response.json()})

    new_token_info = response.json()
    session['access_token'] = new_token_info['access_token']
    session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']

    return redirect('/playlists')


@app.route('/create-playlist', methods=['POST'])
def create_playlist():
    if 'access_token' not in session:
        return jsonify({'error': 'Authentication required'}), 401

    playlist_name = request.form.get('title')
    playlist_description = request.form.get('description')  # Get the description
    songs_text = request.form.get('songs')

    # Check if the 'private' checkbox is checked
    is_private = 'private' in request.form

    if not playlist_name or not songs_text:
        return jsonify({'error': 'Title and songs are required'}), 400

    user_id = spotify.get_user_id(session['access_token'])
    if not user_id:
        return jsonify({'error': 'Could not fetch user information'}), 500

    # The 'public' argument in the create_playlist function should be the inverse of is_private
    playlist = spotify.create_playlist(session['access_token'], user_id, playlist_name, not is_private, playlist_description)

    if 'id' not in playlist:
        return jsonify({'error': 'Failed to create playlist'}), 500

    song_uris = []
    delimiter_pattern = re.compile(r'\d*\.\s*|\s*-\s*|\s*–\s*|\s*:\s*|\s*\|\s*')
    for line in songs_text.split('\n'):
        line = line.strip()  # Trim whitespace from the ends
        if line:
            parts = delimiter_pattern.split(line, 1)
            if len(parts) == 2:
                artist, track_name = map(str.strip, parts)
                uri = spotify.search_track(session['access_token'], track_name, artist)
                if uri:
                    song_uris.append(uri)
                else:
                    print(f"URI not found for track: {track_name} by {artist}")
            else:
                print(f"Invalid line format: {line}")

    if song_uris:
        add_result = spotify.add_tracks_to_playlist(session['access_token'], playlist['id'], song_uris)
        if 'error' in add_result:
            return jsonify({'error': 'Failed to add tracks to the playlist'}), 500

    flash('Playlist created successfully', 'success')
    return jsonify({'redirect': True, 'redirect_url': '/playlists'})

@app.route('/unfollow-playlists', methods=['POST'])
def unfollow_playlists_route():
    if 'access_token' not in session:
        return jsonify({'success': False, 'message': 'Authentication required'}), 401

    playlist_ids = request.json.get('playlistIds')
    if not playlist_ids:
        return jsonify({'success': False, 'message': 'No playlists provided'}), 400

    errors = []
    for playlist_id in playlist_ids:
        success, error = spotify.unfollow_playlist(session['access_token'], playlist_id)
        if not success:
            errors.append({'playlist_id': playlist_id, 'error': error})

    if errors:
        return jsonify({'success': False, 'errors': errors}), 400
    else:
        return jsonify({'success': True, 'message': 'Playlists unfollowed successfully'})

@app.route('/refresh-playlists')
def refresh_playlists():
    if 'access_token' not in session:
        return jsonify({'error': 'Authentication required'}), 401

    response = spotify.get_user_playlists(session['access_token'])
    if response.status_code != 200:
        return jsonify({'error': 'Failed to retrieve playlists'}), 500

    return jsonify(response.json().get('items', []))

# Entering the songs realm
@app.route('/get-playlist-details')
def get_playlist_details():
    playlist_id = request.args.get('playlist_id')
    if not playlist_id:
        return jsonify({'error': 'Playlist ID is required'}), 400

    if 'access_token' not in session:
        return jsonify({'error': 'Authentication required'}), 401

    # Fetch playlist details
    response = spotify.get_playlist_details(session['access_token'], playlist_id)
    if response.status_code != 200:
        logging.error(f"Failed to retrieve playlist details: {response.json()}")
        return jsonify({'error': 'Failed to retrieve playlist details'}), 500

    # This is where we store the playlist details
    playlist_details = response.json()

    # Fetch playlist cover image
    cover_response = spotify.get_playlist_cover_image(session['access_token'], playlist_id)
    if cover_response.status_code == 200:
        cover_images = cover_response.json()
        if cover_images:
            playlist_details['cover_image_url'] = cover_images[0]['url']
        else:
            logging.info(f"No cover image found for playlist: {playlist_id}")
    else:
        logging.error(f"Failed to retrieve playlist cover image: {cover_response.json()}")
        return jsonify({'error': 'Failed to retrieve playlist cover image'}), 500

    return jsonify(playlist_details)


#route get-playlist-songs
@app.route('/get-playlist-songs')
def get_playlist_songs():
    playlist_id = request.args.get('playlist_id')
    if not playlist_id:
        return jsonify({'error': 'Playlist ID is required'}), 400

    if 'access_token' not in session:
        return jsonify({'error': 'Authentication required'}), 401

    response = spotify.get_playlist_songs(session['access_token'], playlist_id)
    if response.status_code != 200:
        return jsonify({'error': 'Failed to retrieve playlist songs'}), 500

    return jsonify(response.json().get('items', []))


# Logout route to clear the session
@app.route('/logout')
def logout():
    session.clear()  # Clear the session to log out the user
    return redirect('/')  # Redirect to the home page or login page
