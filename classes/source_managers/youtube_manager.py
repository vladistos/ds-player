import youtube_dl

from classes.source_managers.ffmpeg_audio import PlayableAudio, AudioMeta
from classes.source_managers.source_manager import SourceManager, Playlist


class YoutubeSourceManager(SourceManager):
    format_options = {
        'format': 'bestaudio/best',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0'
    }

    @classmethod
    def to_playable_audio(cls, **kwargs) -> PlayableAudio:
        info = AudioMeta(kwargs['title'])
        source = kwargs['url']
        info.duration = kwargs['duration']
        info.author = kwargs['channel']
        info.photo = kwargs['thumbnail']
        return PlayableAudio(source, meta_info=info)

    @classmethod
    def search_youtube(cls, query, count):
        with youtube_dl.YoutubeDL(cls.format_options) as ydl:
            if not cls.validate_url(query):
                result = ydl.extract_info(f"ytsearch{count}:{query}", download=False)
                elements = result['entries']
            else:
                elements = [ydl.extract_info(query, download=False)]
        elements = [cls.to_playable_audio(**e) for e in elements]
        return elements

    @classmethod
    def get_track(cls, query) -> PlayableAudio:
        return cls.search_youtube(query, 1)[0]

    @classmethod
    def search_tracks(cls, query) -> list[PlayableAudio]:
        return cls.search_youtube(query, 30)

    def get_playlist(self, query) -> Playlist:
        pass
