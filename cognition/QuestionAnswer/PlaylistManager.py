import os
import random
import qi


proxies = [
    "ALAudioPlayer",
]

class TrackData:

    def __init__(self, file, filepath):

        tmp = file.split("__")

        self.title = tmp[0].replace("_", " ")
        self.artist = tmp[1].replace("_", " ").replace(".ogg", " ")

        self.filepath = filepath

class PlaylistManager:

    def __init__(self, app, music_directory=None):

        self.app = app
        self.logger = qi.Logger("PlaylistManager")
        self.music_directory = music_directory
        self.player = None
        self.initialised = False
        self.playlist = []

    def initialisePlaylist(self):

        if self.initialised:
            return

        self.logger.info("Initialising playlist")

        self.player = self.app.session.service(proxies[0])

        self.logger.info("Playlist location: {}".format(self.music_directory))

        if self.music_directory is None:
            self.logger.error("Music directory not initialised")
            raise ValueError("Music directory not initialised")
        if not os.path.exists(self.music_directory):
            self.logger.error("Music directory does not exist")
            raise ValueError("Music directory does not exist")
        if not os.path.isdir(self.music_directory):
            self.logger.error("Music directory is not a directory")
            raise ValueError("Music directory is not a directory")

        for file in os.listdir(self.music_directory):

            if file.endswith(".ogg"):
                #preloaded = self.player.playFile(os.path.join(self.music_directory, file))
                self.playlist.append(TrackData(file, os.path.join(self.music_directory, file)))
                self.logger.info("Added {} to playlist".format(file))

        self.logger.info("Initialised playlist")
        self.initialised = True

    def playTrack(self):

        track_index = random.randint(0, len(self.playlist)-1)

        self.player.playFile(self.playlist[track_index].filepath)

        return self.playlist[track_index].title, self.playlist[track_index].artist
