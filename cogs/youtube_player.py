import json
from typing import Optional, Union

from discord import slash_command, ApplicationContext, Interaction
from wavelink import Track, YouTubeTrack, YouTubePlaylist

from classes.player_provider import PlayerProvider
from classes.source_managers.ffmpeg_audio import PlayableAudio
from classes.source_managers.youtube_manager import YoutubeSourceManager


class YoutubePlayer:

    @staticmethod
    async def _get_track(q: str, return_first: bool = True) -> Optional[list[PlayableAudio]]:
        if len(q) == 0:
            return None
        try:
            track = YoutubeSourceManager.get_track(q)
            song_s = [track]
        except Exception as e:
            print(e)
            song_s = (await YouTubePlaylist.search(query=q)).tracks
        return song_s

    async def play(self, ctx: Union[ApplicationContext, Interaction], query: str):
        track = await self._get_track(query)
        player = await PlayerProvider.from_context(ctx)
        player.add_to_queue(*track, start_playing=True)