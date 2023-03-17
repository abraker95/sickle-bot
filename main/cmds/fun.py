import discord
import config
import requests

from main import DiscordCmdBase



class CmdsFun:

    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        example = f'{config.cmd_prefix}boom',
        help    = 
            'Sets off a bomb'
    )
    async def boom(self : discord.Client, msg : discord.Message):
        pass
