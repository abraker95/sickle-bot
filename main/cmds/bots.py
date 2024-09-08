import discord
import aiohttp
import asyncio
import warnings

from main import DiscordCmdBase, DiscordBot


class CmdsApi:
    """
    Commands for other bots: DiscordBot -> [external]
    """

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

        if 'msg' in reply:
            txt = str(reply['msg'])
        else:
            txt = 'Done' if reply['status'] == 0 else 'Failed'

        txt = f'```\n{txt}\n```'

        match reply['status']:
            case -1: embed = discord.Embed(color=0x880000, description=txt)
            case  0: embed = discord.Embed(color=0x008800, description=txt)
            case  _: embed = discord.Embed(color=0x880088, description=txt)

        await msg.channel.send(None, embed=embed)
