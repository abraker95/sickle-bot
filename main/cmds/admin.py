import discord
import config
import aiohttp
import asyncio
import warnings

from main import DiscordCmdBase, DiscordBot


class CmdsAdmin:

    @DiscordCmdBase.DiscordCmd(
        example = f'{config.cmd_prefix}kill',
        help    = 
            'Forcefully kill the bot.'
    )
    async def kill(self: DiscordBot, msg: discord.Message, *args: str):
        if msg.author.id != config.admin_user_id:
            status = discord.Embed(title=':skull_crossbones: Sigma Shutting Down.', color=0x808080)
            await msg.channel.send(None, embed=status)

            await asyncio.sleep(3)

            await msg.channel.send('Just kidding, you have no admin permission.')
            return

        status = discord.Embed(title=':skull_crossbones: Sigma Shutting Down.', color=0x808080)
        await msg.channel.send(None, embed=status)
    
        # Shutdown the discord client
        await self.close()

        async with aiohttp.ClientSession() as session:
            # Shutdown the Feed server as well
            async with session.put('http://127.0.0.1:5000/internal', timeout=1, json={
                'shutdown' : True
            }) as response:
                if response.status != 200:
                    warnings.warn('Could not contact feed server')
                    return

                data = await response.json()
                if data['status'] != 'ok':
                    warnings.warn('Feed server shutdown failed')
                    return


    @DiscordCmdBase.DiscordCmd(
        example = f'{config.cmd_prefix}feed.ping',
        help    = 
            'Pings the feed server.'
    )
    async def feed_ping(self: DiscordBot, msg: discord.Message, *args: str):
        if msg.author.id != config.admin_user_id:
            status = discord.Embed(title='You must be the bot admin to use this command', color=0x800000)
            await msg.channel.send(None, embed=status)
            return

        async with aiohttp.ClientSession() as session:
            async with session.put('http://127.0.0.1:5000/ping', timeout=1) as response:
                if response.status != 200:
                    status = discord.Embed(title='Feed server not responding', color=0x800000)
                    await msg.channel.send(None, embed=status)
                    return
                
                status = discord.Embed(title='Feed server ok', color=0x008000)
                await msg.channel.send(None, embed=status)
                return


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        example = f'{config.cmd_prefix}evaluate print("hello world")',
        help    = 
            'Executes raw python code. This should be used with caution.'
    )
    async def evaluate(self: DiscordBot, msg: discord.Message, *args: str):
        if msg.author.id != config.admin_user_id: 
            return

        # TODO
        pass
