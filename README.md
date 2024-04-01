# PlexReviewer
Ability to review plex media randomly and decide to delete, keep, or add to watchlist

# Docker Deployment
3 environment variables are needed to start the Plex Reviewer. 

PLEX_URL (Including any http(s) or port)

PLEX_TOKEN (Get this after logging into the WebUI and looking at the XML of a media item)

PLEX_SECTION (The section you want to load for review, for instance Movies

PRESERVE_MEDIA_ROOT (True or False. Relates to how media gets archived)

A volume can be mapped as well to use the delete function. This should be mapped such that the path returned by plex for any piece of media aligns with the container path

# Deletion
Media is added to one of three watchlists. keep,delete,watchlist that is held within the actual section you are reviewing. In the top right corner of the main page is a button to get to the deletion interface or you can see each list directly by going to http://host:500/playlist?name=<<nameofplaylist>>

Once a playlist is loaded, select items to delete and press the delete button. This removes all traces from plex and the filesystem. 

#Archive
If a folder is mapped to /archive or the environment variable ARCHIVE_FOLDER is given, an archive button will be displayed on the playlist page. Archiving moves the entire directory to an archive folder instead of deleting the data, but will still delete the item from plex. 

If PRESERVE_MEDIA_ROOT is True (string), then it will move the folder to /archive/<full original root path>. For example if you have a movie at /nas/media/movies/MOVIE_TITLE, it will move to /archive/nas/media/movies/MOVIE_TITLE

If it is false, it will automatically detect the common root path if multiple files are present and replace the parent folder of the common path with /archive. Taking the example from before, the new file path will be /archive/movies/MOVIE_TITLE
