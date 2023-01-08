from typing import Optional, Union

from discord import ApplicationContext, Interaction

from classes.player import FFMPEGPlayer
from src.const import ErrorTexts


class PlayerProvider:

    @staticmethod
    async def from_context(ctx: Union[ApplicationContext, Interaction]) -> Optional[FFMPEGPlayer]:
        voice = None
        client = None
        if isinstance(ctx, ApplicationContext):
            voice = ctx.author.voice
            client = ctx.voice_client
        if isinstance(ctx, Interaction):
            voice = ctx.user.voice
            client = ctx.guild.voice_client
        channel = voice.channel if hasattr(voice, 'channel') else None
        if channel is None:
            await ctx.respond(content=ErrorTexts.GET_VOICE_FAILED)
            return None
        if client is None:
            try:
                client = await channel.connect(cls=FFMPEGPlayer)
            except Exception as e:
                pass
        return client

