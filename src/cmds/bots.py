import discord
import aiohttp
import asyncio
import warnings

from core import DiscordCmdBase, DiscordBot


class CmdsBots:
    """
    Commands for other bots: DiscordBot -> [external]
    """

    @DiscordCmdBase.DiscordCmd(
        perm    = DiscordCmdBase.ANYONE,
        example = f'{DiscordBot.cmd_prefix}bot.forum <cmd>',
        help    =
            'Access forum bot endpoint'
    )
    async def bot_forum(self: DiscordBot, msg: discord.Message, *args: "list[str]"):
        # Parse args
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

        # Send request to OT Feed Server
        reply = None
        bot_forum_monitor_port = DiscordBot.get_cfg('Core', 'bot_forum_monitor_port')

        async with aiohttp.ClientSession() as session:
            try:
                async with session.put(f'http://127.0.0.1:{bot_forum_monitor_port}/request', timeout=5, json=data) as response:
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

        if 'msg' in reply:
            txt = str(reply['msg'])
        else:
            txt = 'Done' if reply['status'] == 0 else 'Failed'


        # [2024.09.22] TODO: Proper line-by-line parsing + proper formatting splits
        #   ex: ```code``` across multiple chunks
        chunks = [ txt[i : i + 1023] for i in range(0, len(txt), 1023) ]
        for chunk in chunks:

            assert len(chunk) < 2000, f'chunk length is {len(chunk)}'
            await msg.channel.send(chunk)
