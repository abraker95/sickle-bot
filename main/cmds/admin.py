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
            data = { 'shutdown' : True }

            try:
                async with session.put(f'http://127.0.0.1:{config.feed_server_port}/internal', timeout=1, json=data) as response:
                    if response.status != 200:
                        warnings.warn('Could not contact feed relay server')
                        return

                    data = await response.json()
                    if data['status'] != 'ok':
                        warnings.warn('Feed server shutdown failed')
                        return
            except asyncio.TimeoutError:
                await msg.channel.send('Feed server not responding: Timed out')
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
            try:
                async with session.put(f'http://127.0.0.1:{config.feed_server_port}/ping', timeout=1) as response:
                    if response.status != 200:
                        status = discord.Embed(title='Feed server not responding: Not HTTP OK', color=0x800000)
                        await msg.channel.send(None, embed=status)
                        return
            except asyncio.TimeoutError:
                await msg.channel.send('Feed server not responding: Timed out')
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
            status = discord.Embed(title='You must be the bot admin to use this command', color=0x800000)
            await msg.channel.send(None, embed=status)
            return

        # TODO
        pass


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        example = f'{config.cmd_prefix}bot.stats',
        help    = 
            'Prints this bots\'s stats'
    )
    async def bot_stats(self: DiscordBot, msg: discord.Message, *args: str):
        """
        Data fmt:
            "bot_stats" : {
                (msg.guild.id: str) : {
                    "total_msgs" : (int),
                    "user_msgs"  : (int),
                    "total_cmds" : (int),
                }
            }
        """
        if msg.author.id != config.admin_user_id: 
            status = discord.Embed(title='You must be the bot admin to use this command', color=0x800000)
            await msg.channel.send(None, embed=status)
            return

        table = self.get_db_table('bot_stats')
        entry = table.get(doc_id=msg.guild.id)

        if isinstance(entry, type(None)):
            status = discord.Embed(title='Bot has no stats saved', color=0x008000)
            await msg.channel.send(None, embed=status)
            return

        stats_str = (
            f'Server ID:            {msg.guild.id}\n'
            f'Total msgs processed: {entry["total_msgs"]}\n'
            f'User msgs processed:  {entry["user_msgs"]}\n'
            f'Commands processed:   {entry["total_cmds"]}\n'
        )

        reply = discord.Embed(color=0x1abc9c)
        reply.add_field(name=f'Stats', value=f'```yaml\n{stats_str}```')
        await msg.channel.send(None, embed=reply)

