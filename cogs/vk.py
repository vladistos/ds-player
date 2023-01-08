from enum import Enum
from typing import Union

from discord import ApplicationContext, Interaction

from classes.player_provider import PlayerProvider
from classes.source_managers.vk_manager import VkSourceManager


class VkPlayer:

    vk_searcher = VkSourceManager()

    class PlayType(Enum):
        USER = 0
        PLAYLIST = 1

    async def play(self, ctx: Union[ApplicationContext, Interaction], play_type: PlayType, q: str, ):
        tracks = []
        if play_type == self.PlayType.USER:
            tracks = self.vk_searcher.get_user(q).tracks
        if play_type == self.PlayType.PLAYLIST:
            tracks = self.vk_searcher.get_playlist(q).tracks
        player = await PlayerProvider.from_context(ctx)
        player.add_to_queue(*tracks, start_playing=True)
