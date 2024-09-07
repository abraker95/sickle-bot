import discord
import aiohttp
import asyncio
import warnings

from main import DiscordCmdBase, DiscordBot
from main.FeedServer import FeedServer


class CmdsOsu:

    # Cache for quicker access
    __ot_feed_ch_cache = None

    @DiscordCmdBase.DiscordCmd(
        perm    = DiscordCmdBase.ANYONE,
        example = f'{DiscordBot.cmd_prefix}forum.bot <cmd>',
        help    =
            'Access forum bot endpoint'
    )
    async def forum_bot(self: DiscordBot, msg: discord.Message, *args: "list[str]"):
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
                async with session.post(f'http://127.0.0.1:{44444}/api', timeout=1, json=data) as response:
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

        txt = f'```\n{txt}\n```'

        if reply['status'] == -1:  embed = discord.Embed(color=0x880000, description=txt)
        elif reply['status'] == 0: embed = discord.Embed(color=0x008800, description=txt)
        else:                      embed = discord.Embed(color=0x880088, description=txt)

        await msg.channel.send(None, embed=embed)


    @DiscordCmdBase.DiscordEvent()
    async def forum_bot_feed(self: DiscordBot):
        # [2024.09.07] TODO: Move this to api.py and create a command organization
        await FeedServer.init(lambda data: CmdsOsu.__handle_data(self, data))


    @staticmethod
    async def __handle_data(self: DiscordBot, data: dict):
        required_keys = set((
                'subforum_id',
                'subforum_name',
                'post_date',
                'prev_post_date',
                'thread_title',
                'post_id',
                'first_post_id',
                'username',
                'user_id',
                'avatar_url',
                'contents',
        ))
        if not required_keys.issubset(data):
            warnings.warn(f'Comment data is incomplete!\nData: {data.keys()}\nRequired: {required_keys}')
            return

        # Embed character limit
        contents = data['contents'][:5700]

        # Field character limit
        chunks = [ contents[i : i + 1023] for i in range(0, len(contents), 1023) ]

        # Get post & user urls
        post_url = f'https://osu.ppy.sh/community/forums/posts/{data["post_id"]}'
        user_url = f'https://osu.ppy.sh/users/{data["user_id"]}'

        # Patch up default avatar link
        if 'avatar-guest' in data['avatar_url']:
            data['avatar_url'] = f'https://osu.ppy.sh/{data["avatar_url"]}'

        # Set color
        color = 0x1abc9c  # Greenish
        if data['post_id'] == data['first_post_id']:
            color = 0xeeeeee  # First post of thread is white

        # Construct embed
        embed = discord.Embed(color=color, title=f'Subforum: {data["subforum_name"]}', description=f'[{data["thread_title"]}]({post_url})\n')
        embed.set_author(name=data['username'], url=user_url)
        embed.set_thumbnail(url=data['avatar_url'])
        for chunk in chunks:
            embed.add_field(name=f'\u200b', value=chunk, inline=True)
        embed.set_footer(text=data['post_date'])

        # Send
        is_debug = DiscordBot.get_cfg('Core', 'is_debug')
        ot_feed_channel = 'debug-ot-feed' if is_debug else 'ot-feed'

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
        except discord.errors.Forbidden as e:
            await warnings.warn(f'Error posting forum post to channel {channel.name}: {e}')
        except discord.errors.HTTPException as e:
            warnings.warn(f'Error posting forum post: {e} | Contents:\n{contents}')
        except Exception as e:
            warnings.warn(
                f'Unable to send message to #"{ot_feed_channel}";\n'
                f'{data}\n'
                f'{e}\n'
            )
            return

        warnings.warn(f'No #"{ot_feed_channel}" channel found!')
