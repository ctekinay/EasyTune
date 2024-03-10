// Utility functions to show and hide elements
function toggleElementDisplay(element, isVisible) {
    if (element) {
        element.style.display = isVisible ? 'block' : 'none';
    }
}

// Usage Example:
// To show an element:
// toggleElementDisplay(document.getElementById('someElementId'), true);

// To hide an element:
// toggleElementDisplay(document.getElementById('someElementId'), false);

// Function to toggle the modal's visibility
function toggleModal() {
    var modal = document.getElementById('new-playlist-modal');
    if (modal.style.display === 'block') {
        hideElement(modal, false);
    } else {
        showElement(modal, true);
    }
}

function updatePlaylistsUI(playlists) {
    const playlistContainer = document.querySelector('.playlist-grid');
    playlistContainer.innerHTML = ''; // Clear current playlists

    playlists.forEach(playlist => {
        const playlistRow = document.createElement('div');
        playlistRow.classList.add('playlist-row');
        playlistRow.dataset.playlistId = playlist.id;

        playlistRow.innerHTML = `
            <input type="checkbox" class="playlist-select">
            <div class="playlist-title">${playlist.name}</div>
            <div class="playlist-tracks">${playlist.tracks.total} tracks</div>
            <div class="playlist-creator">${playlist.owner.display_name}</div>
            <div class="playlist-type">${playlist.public ? 'Public' : 'Private'}</div>
        `;

        playlistContainer.appendChild(playlistRow);
    });
}

// Attach a single event listener to the playlist grid container
document.querySelector('.playlist-grid').addEventListener('click', function(event) {
    // Traverse up to find the closest playlist row
    let playlistRow = event.target.closest('.playlist-row');

    if (playlistRow) {
        let playlistId = playlistRow.dataset.playlistId;
        onPlaylistSelect(playlistId);
    }
});

async function onPlaylistSelect(playlistId) {
    console.log('Playlist selected:', playlistId);

    try {
        // Fetch playlist details
        let response = await fetch(`/get-playlist-details?playlist_id=${playlistId}`);
        if (!response.ok) {
            let errorData = await response.json();
            throw new Error('Error fetching playlist details: ' + (errorData.error || response.statusText));
        }

        let playlistDetails = await response.json();

        // Fetch songs after getting playlist details
        response = await fetch(`/get-playlist-songs?playlist_id=${playlistId}`);
        if (!response.ok) {
            let errorData = await response.json();
            throw new Error('Error fetching playlist songs: ' + (errorData.error || response.statusText));
        }

        let songs = await response.json();

        // Call displayPlaylistDetails with both playlistDetails and songs
        displayPlaylistDetails(playlistDetails, songs);

    } catch (error) {
        console.error('Error:', error.message);
        alert('Error: ' + error.message); // Displaying error to the user
    }
}


async function displayPlaylistDetails(playlistDetails, songs) {
    try {

        // Hide or clear elements specific to the playlists screen
        document.getElementById('refresh-playlists').style.display = 'none';
        document.getElementById('delete-selected').style.display = 'none';
        document.getElementById('new-playlist').style.display = 'none';
        document.getElementById('master-select').style.display = 'none';
        document.querySelector('.select-all-header').style.display = 'none';
        document.querySelector('.playlist-container').style.display = 'none';
        // Add more elements to hide or clear as needed

        // Set the playlist metadata
        document.getElementById('playlist-title').textContent = playlistDetails.name || 'No Title';
        document.getElementById('playlist-creator').textContent = `Created by: ${playlistDetails.owner?.display_name || 'Unknown'}`;
        document.getElementById('playlist-type').textContent = `Playlist Type: ${playlistDetails.public ? 'Public' : 'Private'}`;
        document.getElementById('playlist-tracks').textContent = `Tracks: ${playlistDetails.tracks?.total || 0}`;
        document.getElementById('playlist-followers').textContent = `Followers: ${playlistDetails.followers?.total || 0}`;

        // Transition to the playlist details screen
        toggleElementDisplay(document.getElementById('playlist-details'), true);
        toggleElementDisplay(document.querySelector('.playlist-grid'), false);

        // Set the playlist cover image
        const playlistCoverImage = document.getElementById('playlist-cover-image');

        if (playlistDetails && playlistDetails.cover_image_url) {
            playlistCoverImage.src = playlistDetails.cover_image_url; // Set the cover image URL from playlist details
        } else {
            playlistCoverImage.src = '/static/default_playlist_cover.png'; // Set a default image URL
        }

        // Inside the displayPlaylistDetails function
        playlistCoverImage.onload = () => {
            console.log("Image loaded successfully");
        };
        playlistCoverImage.onerror = () => {
            console.error("Failed to load the image");
        };

        // Populate the song list
        const songRowsContainer = document.querySelector('.song-rows');
        songRowsContainer.innerHTML = ''; // Clear any existing songs

        songs.forEach(item => {
            const song = item.track;
            const songRow = document.createElement('div');
            songRow.className = 'song-row';
            songRow.innerHTML = `
                <input type="checkbox" class="song-select">
                <div class="song-title">${song.name}</div>
                <div class="song-artist">${song.artists.map(artist => artist.name).join(', ')}</div>
                <div class="song-album">${song.album.name}</div>
                <div class="song-duration">${formatDuration(song.duration_ms)}</div>
            `;
            songRowsContainer.appendChild(songRow);
        });
    } catch (error) {
        console.error('Error:', error.message);
        alert('Error fetching and displaying playlist details: ' + error.message); // Displaying error to the user
    }
}


async function fetchPlaylists() {
    try {
        let response = await fetch('/refresh-playlists');
        if (!response.ok) {
            let errorData = await response.json();
            throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
        }
        let playlists = await response.json();
        updatePlaylistsUI(playlists);
    } catch (error) {
        console.error('Error:', error.message);
        alert('Error fetching playlists: ' + error.message);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    fetchPlaylists(); // Fetch playlists as soon as the DOM is fully loaded
    setupEventListeners(); // Setup other event listeners
});


// Function to enable or disable the save button
function toggleSaveButton() {
    let title = document.getElementById('playlist-title').value.trim();
    let songs = document.getElementById('playlist-songs').value.trim();
    let saveBtn = document.getElementById('save-playlist-btn');
    saveBtn.disabled = !(title && songs);
    saveBtn.style.opacity = title && songs ? '1' : '0.5';
}

// Event listeners for enabling the save button
document.getElementById('playlist-title').addEventListener('input', toggleSaveButton);
document.getElementById('playlist-songs').addEventListener('input', toggleSaveButton);
document.getElementById('new-playlist-form').addEventListener('submit', handleFormSubmission);

// Event listener for the master select checkbox
document.getElementById('master-select').addEventListener('change', function() {
    var checkboxes = document.querySelectorAll('.playlist-select');
    var masterChecked = this.checked;
    checkboxes.forEach(function(checkbox) {
        checkbox.checked = masterChecked;
    });
});

// Function to delete selected playlists
function deleteSelectedPlaylists() {
    const selectedPlaylists = document.querySelectorAll('.playlist-select:checked');
    const numberOfPlaylistsSelected = selectedPlaylists.length;

    if (numberOfPlaylistsSelected === 0) {
        alert("No playlists selected for deletion.");
        return;
    }

    // Confirmation dialog
    const userConfirmed = confirm(`${numberOfPlaylistsSelected} playlist(s) selected for deletion. Do you confirm?`);

    if (userConfirmed) {
        // User clicked OK, proceed with deletion
        let playlistIds = Array.from(selectedPlaylists).map(checkbox =>
            checkbox.closest('.playlist-row').dataset.playlistId);

        // Call the function to delete playlists from Spotify
        deletePlaylistsFromSpotify(playlistIds);
    }
}

async function deletePlaylistsFromSpotify(playlistIds) {
    try {
        let response = await fetch('/unfollow-playlists', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({playlistIds: playlistIds})
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        let data = await response.json();
        if (data.success) {
            console.log("Playlists successfully deleted from Spotify");
            // Refresh the playlist list
            await fetchPlaylists();
        } else {
            console.error('Failed to delete some playlists:', data.errors);
        }
    } catch (error) {
        console.error('Error:', error);
    }
}


// Event listeners for playlist selection and deletion
document.getElementById('delete-selected').addEventListener('click', deleteSelectedPlaylists);


// Event listener to close the modal when clicking outside of it
window.addEventListener('click', function(event) {
    var modal = document.getElementById('new-playlist-modal');
    if (event.target === modal) {
        hideElement(modal);
    }
});

// Initialization function to set up event listeners after the DOM content is loaded
function setupEventListeners() {
    var modal = document.getElementById('new-playlist-modal');
    var btn = document.getElementById('new-playlist');
    var span = document.getElementsByClassName('close-button')[0];

    btn.onclick = function() {
        toggleElementDisplay(modal, true);
    };

    span.onclick = function() {
        toggleElementDisplay(modal, false);
    };

    const refreshButton = document.getElementById('refresh-playlists');
    if (refreshButton) {
        refreshButton.addEventListener('click', function() {
            fetchPlaylists();
        });
    }

    // Input field listeners for enabling the save button
    document.getElementById('playlist-title').addEventListener('input', toggleSaveButton);
    document.getElementById('playlist-songs').addEventListener('input', toggleSaveButton);
}

// Add this function to handle the form submission
function handleFormSubmission(event) {
    event.preventDefault(); // Prevent the default form submission

    let saveBtn = document.getElementById('save-playlist-btn');
    saveBtn.disabled = true; // Disable the submit button

    var form = document.getElementById('new-playlist-form');
    var formData = new FormData(form);

    // Show a progress message
    var modalContent = document.querySelector('#new-playlist-modal .modal-content');
    var progressMessage = document.createElement('div');
    progressMessage.innerHTML = '<p>Creating playlist, please wait...</p>';
    modalContent.appendChild(progressMessage);

    fetch('/create-playlist', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.redirect) {
            // Redirect to the specified URL
            window.location.href = data.redirect_url;
        } else {
            // Handle other responses here, e.g., display error messages
            console.error('An error occurred:', data.error || 'Unknown error');
            saveBtn.disabled = false; // Re-enable the submit button
            // Remove the progress message
            modalContent.removeChild(progressMessage);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        saveBtn.disabled = false; // Re-enable the button in case of error
        // Remove the progress message
        modalContent.removeChild(progressMessage);
    });
}


// ENTERING THE SONGS REALM


function formatDuration(durationMs) {
    // Convert duration from milliseconds to a formatted string (mm:ss)
    const minutes = Math.floor(durationMs / 60000);
    const seconds = ((durationMs % 60000) / 1000).toFixed(0);
    return minutes + ":" + (seconds < 10 ? '0' : '') + seconds;
}

function setupBackButtonListener() {
        const backButton = document.getElementById('back-to-playlists');
        if (backButton) {
            backButton.addEventListener('click', function() {
                // Actions to perform when the back button is clicked
                const playlistGridContainer = document.querySelector('.playlist-grid');
                const playlistDetailsContainer = document.querySelector('#playlist-details');

                // Hide the playlist details
                document.getElementById('playlist-details').style.display = 'none';
            });
        } else {
            console.error('Back button not found');
        }
    }

// Call setupEventListeners once the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
        // Existing setupEventListeners calls
        setupEventListeners();

        // Set up the back button listener
        setupBackButtonListener();
});
