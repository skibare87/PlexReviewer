from plexapi.server import PlexServer
from flask import Flask, jsonify, request, render_template
import random
import os
import shutil

class PlexLibraryCache:
    url=None
    token=None
    plex=None
    section=None
    library=None
    library_name=''

    def __init__(self,PLEX_URL, PLEX_TOKEN):
        # Create a connection to your Plex server
        self.url=PLEX_URL
        self.token=PLEX_TOKEN
        self.plex = PlexServer(PLEX_URL, PLEX_TOKEN)
        print("Connected to Plex server:", self.plex.friendlyName)
    def loadLibrary(self,LIBRARY_NAME,populate=True):
        # The name of the library from which you want to pick a random item
        self.library_name = 'Movies'
        # Find the library
        self.section = self.plex.library.section(LIBRARY_NAME)
        if populate:
            self.populateLibrary();
    def populateLibrary(self):
        # Fetch all items from the library
        print("Populating")
        self.library = self.section.all()
        print(f'Loaded Library for {self.library_name}')
    def getRandom(self, items=1):
        # Select a random item
        random_list=[]
        for i in range(items):
            random_list.append(random.choice(self.library))
        return random_list
    def getCoverArt(self,plexitem):
        return self.url + plexitem.thumb + "?X-Plex-Token=" + self.token
    def getStorageLocation(self,plexitem):
        return [media_part.file for media in plexitem.media for media_part in media.parts]
    def addToPlaylist(self, playlist_name, ratingKey_to_add):
        playlist = None
        try:
            playlist = self.plex.playlist(playlist_name)
        except Exception as e:
            print(f"Playlist '{playlist_name}' not found. Creating it.")
            playlist = None

        # If the playlist does not exist, create it with the specified media item
        if not playlist:
            media_item = self.plex.fetchItem(str(ratingKey_to_add))
            self.plex.createPlaylist(playlist_name, items=[media_item])
            print(f"Playlist '{playlist_name}' created with the initial media item.")
        else:
            # If the playlist exists, add the specified media item to it
            media_item = self.plex.fetchItem(str(ratingKey_to_add))
            playlist.addItems([media_item])
            print(f"Media item added to the existing playlist '{playlist_name}'.")
    def deleteMedia(self, key):
        item = self.plex.fetchItem(str(key))
        file_paths = [part.file for media in item.media for part in media.parts]
        if len(file_paths) > 0:
            try:
                folder_path = os.path.dirname(file_paths[0])
                shutil.rmtree(folder_path)
            except:
                # Delete files from the filesystem
                for file_path in file_paths:
                    os.remove(file_path)     
        item.delete()
app = Flask(__name__)
@app.route('/')
def index():
    # Render a template that includes JavaScript for swipe detection and AJAX
    if cache is None:
        return render_template('loading.html')
    else:
        return render_template('index.html')
@app.route('/update', methods=['POST'])
def update():
    # Process the swipe direction (left or right) and item's ID
    data = request.json
    direction = data.get('direction')
    item_id = data.get('id')
    # Here, you'd update your data source based on the swipe
    print(f"Item {item_id} was swiped {direction}.")
    return jsonify({"status": "success"})
@app.route('/item')
def get_item():
    # Default number of items to 1 if not specified
    num_items = request.args.get('num', default=1, type=int)
    
    # Your Python code to generate the items' data
    # For demonstration, we'll create dummy data
    def generate_item_data(id):
        media=cache.getRandom()[0]
        return {
            "id": id,
            "key": media.key,
            "ratingkey": media.ratingKey,
            "title": media.title,
            "paths": cache.getStorageLocation(media),
            "description": media.summary,
            "image_url": cache.getCoverArt(media)
        }

    # Handling single or multiple items
    if num_items > 1:
        data = [generate_item_data(i) for i in range(1, num_items + 1)]
    else:
        data = generate_item_data(1)  # Single item
    
    return jsonify(data)
@app.route('/addToPlaylist', methods=['POST'])
def addToPlaylist():
    # Parse the JSON data sent with the POST request
    data = request.json

    # Extract playlist name and rating key from the data
    playlist_name = data.get('playlist_name')
    rating_key_to_add = data.get('rating_key')

    # Ensure both playlist name and rating key are provided
    if not playlist_name or not rating_key_to_add:
        return jsonify({'error': 'Missing playlist_name or rating_key'}), 400

    # Call the method to add the item to the playlist
    try:
        cache.addToPlaylist(playlist_name, rating_key_to_add)
        return jsonify({'message': f'Item with rating key {rating_key_to_add} added to playlist "{playlist_name}".'}), 200
    except Exception as e:
        # Handle errors (e.g., item or playlist not found)
        print(e)
        return jsonify({'error': str(e)}), 500
@app.route('/playlist')
def playlist_contents():
    playlist_name = request.args.get('name')  # Get the playlist name from the URL query parameter
    playlist = cache.plex.playlist(playlist_name)
    items = [{
        'title': item.title,
        'key': item.key, 
        'file_paths': [part.file for media in item.media for part in media.parts]
    } for item in playlist.items()]
    return render_template('playlist.html', items=items, playlist_name=playlist_name)
@app.route('/delete-items', methods=['POST'])
def delete_items():
    data = request.json
    print(str(data))
    keys = data.get('keys', [])
    
    for key in keys:
        try:
            cache.deleteMedia(key)
        except OSError as e:
            return jsonify({'message': f'Failed to delete file: {file_path}, Error: {str(e)}'}), 500

    return jsonify({'message': 'Selected items deleted successfully'}), 200
PLEX_URL = os.getenv('PLEX_URL', 'http://localhost:32400')
PLEX_TOKEN = os.getenv('PLEX_TOKEN', '')
SECTION = os.getenv('PLEX_SECTION', 'Movies')


cache = PlexLibraryCache(PLEX_URL, PLEX_TOKEN)
cache.loadLibrary(SECTION)
    
if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0")

