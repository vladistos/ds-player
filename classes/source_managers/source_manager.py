import re
from abc import ABCMeta, abstractmethod
from typing import Optional

from classes.source_managers.ffmpeg_audio import PlayableAudio, AudioMeta


class Playlist:
    def __init__(self, tracks: list[PlayableAudio], info: Optional[AudioMeta]):
        self.tracks = tracks
        self.info = info


class SourceManager(metaclass=ABCMeta):

    @abstractmethod
    def get_track(self, query) -> PlayableAudio:
        pass

    @abstractmethod
    def search_tracks(self, query) -> list[PlayableAudio]:
        pass

    @abstractmethod
    def get_playlist(self, query) -> Playlist:
        pass

    @staticmethod
    def validate_url(url):
        regex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        return re.match(regex, url) is not None
