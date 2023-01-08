from discord import Cog, ApplicationContext

from classes.player import FFMPEGPlayer
from classes.player_provider import PlayerProvider
from classes.views import PlayerView


class MusicControllerCog(Cog):
    @classmethod
    async def reply_for_player(cls, player: FFMPEGPlayer, ctx: ApplicationContext):
        if player.view:
            await ctx.respond(content='Готово', ephemeral=True)
            return
        view = PlayerView(player)
        view.message = await ctx.respond(view=view.get_view(), embed=view.get_embed())
        player.view = view


