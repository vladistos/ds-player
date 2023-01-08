from classes.source_managers.ffmpeg_audio import PlayableAudio, AudioMeta
from classes.source_managers.source_manager import SourceManager, Playlist
import requests

from src.const import Constants


class VkApi:
    def __init__(self, token):
        self.token = token
        self.params = {
            'access_token': self.token,
            'count': 10000,
            'v': '5.111'
        }

    def get_user_audio(self, user_id):
        params = self.params.copy()
        params['user_id'] = user_id
        resp = requests.get('https://api.vk.com/method/audio.get', params=params).json()
        tracks = [VkSourceManager.to_playable_audio(**item) for item in resp['response']['items']]
        playlist = Playlist(tracks, None)
        return playlist

    def get_playlist_audio(self, playlist_link: str):
        pid = 0
        poid = 0
        if 'audio_playlist' in playlist_link:
            (poid, pid) = playlist_link.split('audio_playlist')[1].split('%')[0].split('&')[0].split('_')
        elif 'album' in playlist_link:
            (poid, pid) = playlist_link.split('album/')[1].split('_')[0:1]
        params = self.params.copy()
        params['album_id'] = pid
        params['owner_id'] = poid
        print(params)
        resp = requests.get('https://api.vk.com/method/audio.get', params=params).json()
        tracks = [VkSourceManager.to_playable_audio(**item) for item in resp['response']['items']]
        playlist = Playlist(tracks, None)
        return playlist


class VkSourceManager(SourceManager):

    vk_api = VkApi(Constants.VK_TOKEN)

    @classmethod
    def to_playable_audio(cls, **kwargs):
        info = AudioMeta(kwargs['title'])
        source = kwargs['url']
        info.author = kwargs['artist']
        info.duration = kwargs['duration']
        thumb = None
        album = kwargs.get('album')
        if album is not None:
            thumb = album.get('thumb')

        if thumb is not None:
            info.photo = thumb['photo_1200']
        return PlayableAudio(source, meta_info=info)

    def get_track(self, query) -> PlayableAudio:
        pass

    def search_tracks(self, query) -> list[PlayableAudio]:
        pass

    def get_playlist(self, query):
        return self.vk_api.get_playlist_audio(query)

    def get_user(self, uid):
        return self.vk_api.get_user_audio(uid)
