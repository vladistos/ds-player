from discord import slash_command, ApplicationContext

from classes.player_provider import PlayerProvider
from classes.source_managers.audiofilters import TempoFilter
from classes.source_managers.ffmpeg_audio import PlayableAudio, AudioMeta
from classes.views import PlayerView
from cogs.music_base import MusicControllerCog


class MusicControl(MusicControllerCog):

    TEST_AUDIO = PlayableAudio(
        source='https://cs1-82v4.vkuseraudio.net/s/v1/acmp/WY7gR6Ntw2Q_'
               'fA801Ocn79H50P-SYxPKNHVNn-BpQEiidzqiwTeISFPweGbdu666R9Ay'
               'RG3qpYuuHL7ixBsBW1PKOk-kIWyh48qiaYPklfa42pg9wBwktitB9g-Oy'
               '9z5GG4y0cpjTno9wMKo1P1WdLoR2Uh-U-6NkGTqb-Ea4bQSefiSqA.mp3',
        meta_info=AudioMeta(title='test'))

    @slash_command(name='player')
    async def player(self, ctx: ApplicationContext):
        c = await PlayerProvider.from_context(ctx)
        view = PlayerView(c)
        await ctx.respond(view=view.get_view(), embed=view.get_embed())
