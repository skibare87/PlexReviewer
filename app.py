from plexapi.server import PlexServer
from flask import Flask, jsonify, request, render_template
from collections import defaultdict
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
    def getLibraryName(self):
        return str(self.library_name)
    def loadLibrary(self,LIBRARY_NAME,populate=True):
        # The name of the library from which you want to pick a random item
        self.library_name = LIBRARY_NAME.lower()
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
        return self.getPaths(plexitem)
    def addToPlaylist(self, playlist_name, ratingKey_to_add):
        playlist = None
        try:
            playlist = self.plex.playlist(playlist_name)
            if len(playlist.items()) == 0:
                playlist.delete()
                playlist=None
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
    def getPaths(self, item):
        # Initialize an empty list to hold all file paths
        file_paths = []

        #  Check if the item is a movie
        if item.type == 'movie':
            file_paths = [part.file for media in item.media for part in media.parts]

        # Check if the item is a TV show
        elif item.type == 'show':
            # Iterate through each season of the show
            for season in item.seasons():
                # Iterate through each episode in the season
                for episode in season.episodes():
                    # Iterate through each part of the episode (there could be multiple files per episode)
                    file_paths.extend([part.file for media in episode.media for part in media.parts])

        # At this point, file_paths will contain the paths for a movie or all episodes of a TV show
        return file_paths
    def findCommonRoot(self,file_paths):
        if not file_paths:
            return ""

        # Split each path into components
        path_components = [path.split(os.sep) for path in file_paths]

        # Zip together all path components to make them easier to compare
        zipped_components = zip(*path_components)

        common_path_parts = []
        for component_group in zipped_components:
            if all(component == component_group[0] for component in component_group):
                common_path_parts.append(component_group[0])
            else:
                break  # Stop at the first non-matching component

        # Join the common components back into a path
        common_root=os.sep.join(common_path_parts)
        if os.path.isfile(common_root):
            parent_directory = os.path.dirname(common_root)
        else:
            parent_directory = common_root
        return parent_directory

    def archiveMedia(self, key, preserve_root):
        item = self.plex.fetchItem(str(key))
        if item.TYPE == 'episode':
            item=item.show()
        file_paths = self.getPaths(item)
        common_root=self.findCommonRoot(file_paths)
        if not preserve_root:
            targetdir=common_root.lstrip(os.sep).replace(os.path.dirname(common_root), "/archive/",1)
        else:
            targetdir = os.path.join("/archive", common_root.lstrip(os.sep))
        try:
            os.makedirs(os.path.dirname(targetdir), exist_ok=True)
            print(f'Moving {common_root} to {targetdir}')
            shutil.move(common_root, os.path.dirname(targetdir))
            item.delete()
            return True
        except Exception as e:
            print(f"An error occurred: {e}")
            return False
    def deleteMedia(self, key):
        item = self.plex.fetchItem(str(key))
        if item.TYPE == 'episode':
            item=item.show()
        file_paths = self.getPaths(item)

        if len(file_paths) > 0:
            try:
                folder_path = os.path.dirname(file_paths[0])
                shutil.rmtree(folder_path)
                while os.path.exists(os.path.dirname(folder_path)) and len(os.listdir(os.path.dirname(folder_path))) == 0:
                    parent_folder = os.path.dirname(folder_path)
                    # Break if parent_folder is the same as folder_path to prevent infinite loop
                    if parent_folder == folder_path or not os.path.exists(parent_folder):
                        break
                    # If the parent is empty, remove it
                    if len(os.listdir(parent_folder)) == 0:
                        shutil.rmtree(parent_folder)
                        folder_path = parent_folder
                    else:
                        break
            except:
                # Delete files from the filesystem
                for file_path in file_paths:
                    if os.path.exists(file_path):
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
    playlist_name = data.get('playlist_name')+"_"+cache.getLibraryName()
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
    playlist_name = request.args.get('name')+"_"+cache.getLibraryName()  # Get the playlist name from the URL query parameter
    try:
        playlist = cache.plex.playlist(playlist_name)
        

        # Step 1: Initialize a dictionary to aggregate episodes by their shows
        shows = defaultdict(lambda: {"title": None, "key": None, "file_paths": set()})

        # Step 2: Iterate through the playlist items and aggregate
        for item in playlist.items():
            if item.TYPE == 'episode':
                # Assuming 'show()' method fetches the show object for the episode
                show = item.show()
            else:
                show=item
            show_title = show.title
            show_key = show.key
            
            shows[show_key]["title"] = show_title  # Update the title (redundant after the first episode of each show)
            shows[show_key]["key"] = show_key  # Update the show key (redundant after the first episode of each show)
            # Aggregate file paths; convert to list if you prefer, but sets avoid duplicates
            shows[show_key]["file_paths"].update(
                part.file for media in item.media for part in media.parts
            )
        # Step 3: Convert the aggregation to a list
        items = [
            {
                "title": data["title"],
                "key": show_key,
                # Convert the set of file paths to a list, if necessary
                "file_paths": [cache.findCommonRoot(list(data["file_paths"]))]
            }
            for show_key, data in shows.items()
        ]

        # items = [{
            # 'title': item.grandparentTitle + ": " + item.title if item.TYPE == 'episode' else item.title,
            # 'key': item.key, 
            # 'file_paths': [part.file for media in item.media for part in media.parts]
        # } for item in playlist.items()]
    except Exception as e:
        print(e)
        items=[]
    
    return render_template('playlist.html', items=items, playlist_name=playlist_name, archive_exists=archive_exists)
@app.route('/archive-items', methods=['POST'])
def archive_items():
    data = request.json
    #print(str(data))
    keys = data.get('keys', [])
    
    for key in keys:
        try:
            if cache.archiveMedia(key, PRESERVE_ROOT):
                return jsonify({'message': 'Selected items archived successfully'}), 200
            else:
                return jsonify({'message': f'Failed to archive file: {key}'}), 500
        except OSError as e:
            return jsonify({'message': f'Failed to archive file: {key}, Error: {str(e)}'}), 500

    return jsonify({'message': 'Selected items archived successfully'}), 200
@app.route('/delete-items', methods=['POST'])
def delete_items():
    data = request.json
    #print(str(data))
    keys = data.get('keys', [])
    
    for key in keys:
        try:
            cache.deleteMedia(key)
        except OSError as e:
            return jsonify({'message': f'Failed to delete file: {key}, Error: {str(e)}'}), 500

    return jsonify({'message': 'Selected items deleted successfully'}), 200
PLEX_URL = os.getenv('PLEX_URL', 'http://localhost:32400')
PLEX_TOKEN = os.getenv('PLEX_TOKEN', '')
SECTION = os.getenv('PLEX_SECTION', 'Movies')
PRESERVE_ROOT = not os.getenv("PRESERVE_MEDIA_ROOT", "False").lower().startswith('f')
if os.path.exists('/archive'):
    archive_exists=True
elif "ARCHIVE_FOLDER" in os.environ and os.path.isdir(os.environ["ARCHIVE_FOLDER"]):
    try:
        os.symlink(os.environ["ARCHIVE_FOLDER"], "/archive")
        if os.path.exists('/archive'):
            archive_exists=True
        else:
            archive_exists=False
            print("Failed to link Archive Folder")
    except OSError as e:
        print(f"Failed to create symlink: {e}")
else:
    archive_exists=False

cache = PlexLibraryCache(PLEX_URL, PLEX_TOKEN)
cache.loadLibrary(SECTION)
    
if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0")

