# PlexReviewer
Ability to review plex media randomly and decide to delete, keep, or add to watchlist

# Docker Deployment
3 environment variables are needed to start the Plex Reviewer. 
PLEX_URL
PLEX_TOKEN (Get this after logging into the WebUI and looking at the XML of a media item)
PLEX_SECTION (The section you want to load for review, for instance Movies

A volume can be mapped as well to use the delete function. This should be mapped such that the path returned by plex for any piece of media aligns with the container path

# Deletion
Media is added to one of three watchlists. keep,delete,watchlist that is held within the actual section you are reviewing. In the top right corner of the main page is a button to get to the deletion interface or you can see each list directly by going to http://host:500/playlist?name=<<nameofplaylist>>

Once a playlist is loaded, select items to delete and press the delete button. This removes all traces from plex and the filesystem. 

