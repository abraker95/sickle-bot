import discord
import config
import aiohttp
import asyncio
import warnings

import tinydb
from tinydb.table import Document

import datetime
import config

from main import DiscordCmdBase, DiscordBot
from main.FeedServer import FeedServer


class CmdsOsu:

    # Cache for quicker access
    __ot_feed_ch_cache = None

    @DiscordCmdBase.DiscordCmd(
        perm    = DiscordCmdBase.ANYONE,
        example = f'{config.cmd_prefix}forum.bot <cmd>',
        help    =
            'Access forum bot endpoint'
    )
    async def forum_bot(self: DiscordBot, msg: discord.Message, *args: str):
        # Parse args
        if len(args) < 1:
            await self.run_help_cmd(msg, 'forum.bot')
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

        # Send request to OT Feed Server
        reply = None

        async with aiohttp.ClientSession() as session:
            try:
                async with session.put(f'http://127.0.0.1:{44444}/request', timeout=1, json=data) as response:
                    if response.status != 200:
                        await msg.channel.send('Failed')
                        return

                    reply = await response.json()
            except asyncio.TimeoutError:
                await msg.channel.send('Timed out')
                return

        # Parse reply from OT Feed Server
        if isinstance(reply, type(None)):
            warnings.warn('Received invalid reply from OT Feed Server: None')
            await msg.channel.send('Received invalid reply from OT Feed Server')
            return

        if not 'status' in reply:
            warnings.warn(f'Received invalid reply from OT Feed Server: {reply}')
            await msg.channel.send('Received invalid reply from OT Feed Server')
            return

        if 'msg' in reply: txt = str(reply['msg'])
        else:              txt = 'Done' if reply['status'] == 0 else 'Failed'

        if reply['status'] == -1:  embed = discord.Embed(color=0x880000, description=txt)
        elif reply['status'] == 0: embed = discord.Embed(color=0x008800, description=txt)
        else:                      embed = discord.Embed(color=0x880088, description=txt)

        await msg.channel.send(f'```\n{txt}\n```')


    @DiscordCmdBase.DiscordEvent()
    async def forum_bot_feed(self: DiscordBot):
        await FeedServer.init(lambda data: CmdsOsu.__handle_data(self, data))


    @staticmethod
    async def __handle_data(self: DiscordBot, data: dict):
        new_link = f'https://osu.ppy.sh/community/forums/posts/{data["post_id"]}'

        avatar_url = data['avatar'] if data['avatar'] != '' else None
        user_url   = data['user_profile'] if data['user_profile'] != '' else None
        timestamp  = datetime.datetime.strptime(data['time'].split('+')[0], '%Y-%m-%d %H:%M:%S')

        embed = discord.Embed(color=0x1ABC9C, timestamp=timestamp)
        embed.set_author(name=data['user'], url=user_url, icon_url=avatar_url)
        embed.add_field(name=data['thread_title'], value=new_link)

        ot_feed_channel = 'debug-ot-feed' if 'db' in config.runtime_mode else 'ot-feed'

        try:
            # If channel is cached
            if not isinstance(CmdsOsu.__ot_feed_ch_cache, type(None)):
                await CmdsOsu.__ot_feed_ch_cache.send(embed=embed)
                return

            # Otherwise look for it
            for server in self.guilds:
                for channel in server.channels:
                    if channel.name == ot_feed_channel:
                        CmdsOsu.__ot_feed_ch_cache = channel
                        await channel.send(embed=embed)
                        return
        except Exception as e:
            warnings.warn(
                f'Unable to send message to #"{ot_feed_channel}";\n'
                f'{data}\n'
                f'{e}\n'
            )
            return

        warnings.warn(f'No #"{ot_feed_channel}" channel found!')
