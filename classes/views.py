import asyncio
from datetime import timedelta
from typing import Dict, Any, Optional

from discord import Interaction, Embed, ButtonStyle
from discord.ui import View, Item, Button, Modal, InputText
from wavelink import Player
from wavelink.abc import Playable

from classes.player import FFMPEGPlayer
from classes.source_managers.audiofilters import *
from classes.source_managers.ffmpeg_audio import PlayableAudio
from cogs.vk import VkPlayer
from cogs.youtube_player import YoutubePlayer
from src.const import ReplyTexts
from classes.player_provider import PlayerProvider


class EmptyTrack(Playable):
    def __init__(self):
        info = {'title': 'Сейчас ничего не играет'}
        super().__init__('-1', info)


class PlayerWrapper:
    def __init__(self, player: FFMPEGPlayer, ):
        self._player = player

        self.is_paused = player.is_paused

    @property
    def source(self) -> PlayableAudio:
        return self._player.source

    @property
    def source_data(self):
        return self.source.meta_info if self.source else None


class PlayerView:
    def __init__(self, player: FFMPEGPlayer):
        self._view = View()
        self._embed = Embed()
        self._player_wrapper: PlayerWrapper = PlayerWrapper(player)
        player.on_track_ended_callback = self.refresh_async
        self.timeout = None
        self.message = None
        self.construct()

    def get_view(self) -> View:
        return self._view

    def get_embed(self) -> Embed:
        return self._embed

    def construct_embed(self, player_wrapper=None):
        if player_wrapper:
            self._player_wrapper: PlayerWrapper = player_wrapper
        self._embed = Embed()
        image = 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTrWPPrq67V-Hc98tMBNxjxQ4xgPwUVbiwApg&usqp=CAU'
        if self._player_wrapper.source_data:
            self._embed.title = 'Now playing'

            self._embed.add_field(name=ReplyTexts.lined(self._player_wrapper.source_data.author),
                                  value=ReplyTexts.lined(self._player_wrapper.source_data.title), inline=True)

            image = self._player_wrapper.source_data.photo

            if not image:
                image = 'https://professional.dolby.com/siteassets/professional-blocks/icons/music.png'
        else:
            self._embed.title = 'Nothing playing now'

        self._embed.set_image(url=image)

    def construct_view(self, player_wrapper=None):
        if player_wrapper:
            self._player_wrapper: PlayerWrapper = player_wrapper
        pp_button = self.get_pp_button()
        button_next = self.get_next_button()
        button_prev = self.get_prev_button()
        shuffle_button = self.get_shuffle_button()
        v = View(self.get_clear_button(), button_prev, pp_button, button_next, shuffle_button,
                 self.get_filter_button(DelayFilter(), 'Delay'),
                 self.get_filter_button(ReverseFilter(), 'Reverse'),
                 self.get_filter_button(TempoFilter, 'Tempo', ['Tempo (1.0 - normal)']),
                 self.get_filter_button(VolumeFilter, 'Volume', ['Volume (1.0 - normal)']),
                 self.get_vk_user_button(), self.get_vk_playlist_button(), self.get_yt_video_button())

        v.timeout = None
        self._view = v

    def construct(self, player_wrapper=None):
        if player_wrapper:
            self._player_wrapper: PlayerWrapper = player_wrapper
        self.construct_view()
        self.construct_embed()

    def refresh_async(self):
        pass

    def get_vk_user_button(self):
        btn = Button()
        btn.style = ButtonStyle.blurple
        btn.label = 'Vk user'
        btn.row = 2

        async def callback(i: Interaction):
            modal = Modal(title='Type user id')
            inp = InputText(label='user id')

            async def modal_callback(i1: Interaction):
                await VkPlayer().play(i1, VkPlayer.PlayType.USER, modal.children[0].value)
                await self.refresh_self(i)
                await i1.response.defer()

            modal.callback = modal_callback
            modal.add_item(inp)
            await i.response.send_modal(modal)

        btn.callback = callback
        return btn

    def get_vk_playlist_button(self):
        btn = Button()
        btn.style = ButtonStyle.blurple
        btn.label = 'Vk playlist'
        btn.row = 2

        async def callback(i: Interaction):
            modal = Modal(title='Type playlist link')
            inp = InputText(label='Playlist link')

            async def modal_callback(i1: Interaction):
                await VkPlayer().play(i1, VkPlayer.PlayType.PLAYLIST, modal.children[0].value)
                await self.refresh_self(i)
                await i1.response.defer()

            modal.callback = modal_callback
            modal.add_item(inp)
            await i.response.send_modal(modal)

        btn.callback = callback
        return btn

    def get_yt_video_button(self):
        btn = Button()
        btn.style = ButtonStyle.red
        btn.label = 'Youtube video'
        btn.row = 2

        async def callback(i: Interaction):
            modal = Modal(title='Video link / query')
            inp = InputText(label='Video link / query')

            async def modal_callback(i1: Interaction):
                await YoutubePlayer().play(i1, modal.children[0].value)
                await self.refresh_self(i)
                await i1.response.defer()

            modal.callback = modal_callback
            modal.add_item(inp)
            await i.response.send_modal(modal)

        btn.callback = callback
        return btn

    async def refresh_self(self, interaction: Interaction = None):
        if interaction:
            self.message = interaction.message
        if not self._player_wrapper:
            player = await PlayerProvider.from_context(interaction)
            self._player_wrapper = PlayerWrapper(player)
        self.construct(self._player_wrapper)
        await self.message.edit(view=self._view, embed=self._embed)

    async def filter_callback(self, interaction: Interaction, _filter: AudioFilter, force=False):
        player = await PlayerProvider.from_context(interaction)
        if _filter not in player.filters:
            player.filters.append(_filter)
            player.set_filters(*player.filters)
        else:
            player.filters.remove(_filter)
            if force:
                player.filters.append(_filter)
            player.set_filters(*player.filters)

        await interaction.response.defer()
        await self.refresh_self(interaction)

    async def filter_callback_with_modal(self, interaction: Interaction, filter_callable, filter_options: list[str]):
        modal = Modal(title='Filter options')
        for o in filter_options:
            modal.add_item(InputText(label=o))

        async def callback(i: Interaction):
            await self.filter_callback(i, filter_callable(*[i.value for i in modal.children]), True)

        modal.callback = callback

        await interaction.response.send_modal(modal)

    def get_clear_button(self):
        btn = Button()
        btn.label = '❌'

        async def callback(i: Interaction):
            player = await PlayerProvider.from_context(i)
            player.queue.track_list.clear()
            await i.response.defer()
            await self.refresh_self(i)

        btn.callback = callback
        return btn

    def get_filter_button(self, filter_: AudioFilter, label: str, options: Optional[list[str]] = None):
        btn = Button()
        btn.label = label
        btn.row = 1

        if self._player_wrapper and self._player_wrapper._player and filter_ in self._player_wrapper._player.filters:
            btn.style = ButtonStyle.blurple
        else:
            btn.style = ButtonStyle.gray

        async def callback(i: Interaction):
            if options:
                await self.filter_callback_with_modal(i, filter_, options)
            else:
                await self.filter_callback(i, filter_)

        btn.callback = callback

        return btn

    """Play pause button"""

    async def pp_button_callback(self, interaction: Interaction):
        player = await PlayerProvider.from_context(interaction)
        player.play_or_pause()
        await self.refresh_self(interaction)
        await interaction.response.defer()

    def get_pp_button(self):
        btn = Button()
        btn.label = '❚❚' if not self._player_wrapper.is_paused() or self._player_wrapper.source_data is None else '▶'
        btn.callback = self.pp_button_callback
        return btn

    """Button next"""

    async def next_button_callback(self, interaction: Interaction):
        player = await PlayerProvider.from_context(interaction)
        player.next_track()
        await self.refresh_self(interaction)
        await interaction.response.defer()

    def get_next_button(self):
        btn = Button()
        btn.label = '⏵'
        btn.callback = self.next_button_callback
        return btn

    """Button previous"""

    async def prev_button_callback(self, interaction: Interaction):
        player = await PlayerProvider.from_context(interaction)
        player.prev_track()
        await self.refresh_self(interaction)
        await interaction.response.defer()

    def get_prev_button(self):
        btn = Button()
        btn.label = '⏴'
        btn.callback = self.prev_button_callback
        return btn

    """Shuffle button"""

    async def shuffle_button_callback(self, interaction: Interaction):
        player = await PlayerProvider.from_context(interaction)
        player.shuffle()
        await self.refresh_self(interaction)
        await interaction.response.defer()

    def get_shuffle_button(self):
        btn = Button()
        btn.label = '⤲'
        btn.callback = self.shuffle_button_callback
        return btn
