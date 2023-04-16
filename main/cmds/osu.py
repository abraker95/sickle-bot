import discord
import config
import requests
import asyncio
import warnings

import tinydb
from tinydb.table import Document

import datetime

from main import DiscordCmdBase, DiscordBot
from main.FeedServer import FeedServer


class CmdsOsu:

    @DiscordCmdBase.DiscordCmd(
        example = f'{config.cmd_prefix}bot.forum <cmd>',
        help    = 
            'Access forum bot endpoint'
    )
    async def bot_forum(self: DiscordBot, msg: discord.Message, *args: str):
        if len(args) < 1:
            await self.run_help_cmd(msg, 'bot.forum')
            return

        try:    bot, name = args[0].split('.')
        except: bot, name = 'Core', 'help'

        data = {
            'bot'  : bot,
            'cmd'  : name,
            'args' : [],
            'key'  : msg.author.id
        }

        if len(args) > 1:
            data['args'] = args[1:]

        success = requests.session().post(f'http://127.0.0.1:{44444}/api', json=data)
        if not success:
            await msg.channel.send('Failed')


    @DiscordCmdBase.DiscordEvent()
    async def forum_bot_feed(self: DiscordBot):
        await FeedServer.init(lambda data: CmdsOsu.__handle_data(self, data))


    @staticmethod
    async def __handle_data(self: DiscordBot, data):
        new_link = f'https://osu.ppy.sh/community/forums/posts/{data["post_id"]}'

        avatar_url = data['avatar'] if data['avatar'] != '' else None
        user_url   = data['user_profile'] if data['user_profile'] != '' else None

        print(data['time'])

        embed = discord.Embed(color=0x1ABC9C, timestamp=parse(data['time']))
        embed.set_author(name=data['user'], url=user_url, icon_url=avatar_url)
        embed.add_field(name=data['thread_title'], value=new_link)

        try:
            for server in self.guilds:
                for channel in server.channels:
                    if channel.name == 'ot-feed':
                        await channel.send(embed=embed)
                        return

            warnings.warn('No ot-feed channel found!')
        except Exception as e:
            warnings.warn(
                f'Unable to send message to ot-feed;\n'
                f'{data}\n'
                f'{e}\n'
            )
