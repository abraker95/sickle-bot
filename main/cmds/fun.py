import discord
import asyncio
import requests
import random

from main import DiscordCmdBase, DiscordBot



class CmdsFun:

    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        perm     = DiscordCmdBase.ANYONE,
        anywhere = True,
        example  = f'{DiscordBot.cmd_prefix}boom',
        help     =
            'Sets off a bomb'
    )
    async def boom(self: DiscordBot, msg: discord.Message, *args: "list[str]"):
        bomb = await msg.channel.send(':bomb:')
        await asyncio.sleep(5)
        await bomb.edit(content=':boom:')


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        perm    = DiscordCmdBase.ANYONE,
        example = f'{DiscordBot.cmd_prefix}xkcd 2',
        help    =
            'Outputs the specified xkcd or a random xkcd if number not specified.'
    )
    async def xkcd(self: DiscordBot, msg: discord.Message, *args: "list[str]"):
        if len(args) > 1:
            await self.run_help_cmd(msg, 'xkcd')
            return

        comic_id = None

        if len(args) == 1:
            try: comic_id = int(args[0])
            except ValueError:
                await msg.channel.send(None, embed=discord.Embed(title=':exclamation: Invalid number', color=0x993333))
                return

        if len(args) <= 0:
            # Grab info of latest comic to get its id
            reply = requests.get('http://xkcd.com/info.0.json')

            if reply.status_code != 200:  # No good
                await msg.channel.send(None, embed=discord.Embed(title=f':exclamation: Error requesting comic (HTTP {reply.status_code}', color=0x993333))
                return

            reply = reply.json()

            try: comic_id = random.randint(1, reply['num'])
            except KeyError:
                await msg.channel.send(None, embed=discord.Embed(title=':exclamation: Error parsing xkcd data', color=0x993333))
                return

        if isinstance(comic_id, type(None)):
            await msg.channel.send(None, embed=discord.Embed(title=':exclamation: Unexpected error', color=0x993333))
            return

        reply = requests.get(f'http://xkcd.com/{comic_id}/info.0.json')
        if reply.status_code == 404:  # Not found
            await msg.channel.send(None, embed=discord.Embed(title=':exclamation: Requested comic does not exist', color=0x993333))
            return

        if reply.status_code != 200:  # No good
            await msg.channel.send(None, embed=discord.Embed(title=f':exclamation: Error requesting comic (HTTP {reply.status_code}', color=0x993333))
            return

        reply = reply.json()

        try:
            embed = discord.Embed(color=0x1abc9c, title=f'🚽 xkcd Comic #{reply["num"]}: {reply["title"]}').set_image(url=reply['img'])
            embed.set_footer(text=reply['alt'])
        except KeyError:
            await msg.channel.send(None, embed=discord.Embed(title=':exclamation: Error parsing xkcd data', color=0x993333))
            return

        await msg.channel.send(None, embed=embed)
