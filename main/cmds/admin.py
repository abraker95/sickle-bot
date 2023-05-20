import discord
import config
import aiohttp
import asyncio
import warnings
import logging
import time
import random
import inspect

from main import DiscordCmdBase, DiscordBot


class CmdsAdmin:

    @DiscordCmdBase.DiscordCmd(
        perm    = DiscordCmdBase.ADMINISTRATOR,
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
        perm    = DiscordCmdBase.ADMINISTRATOR,
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
        perm    = DiscordCmdBase.ADMINISTRATOR,
        example = f'{config.cmd_prefix}eval print("hello world")',
        help    =
            'Executes raw python code. This should be used with caution.'
    )
    async def eval(self: DiscordBot, msg: discord.Message, *args: str):
        if msg.author.id != config.admin_user_id:
            status = discord.Embed(title='You must be the bot admin to use this command', color=0x800000)
            await msg.channel.send(None, embed=status)
            return

        if len(args) == 0:
            await self.run_help_cmd(msg, 'eval')
            return

        output = eval(' '.join(args))
        if inspect.isawaitable(output):
            output = await output

        status = discord.Embed(title='✅ Executed', color=0x66CC66)
        if output:
            status.add_field(name='Results', value=f'\n```\n{output}\n```')
        await msg.channel.send(None, embed=status)


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        perm    = DiscordCmdBase.ADMINISTRATOR,
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



    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        perm    = DiscordCmdBase.ADMINISTRATOR,
        example = f'{config.cmd_prefix}cmd.stats.all',
        help    =
            'Prints this bots\'s stats'
    )
    async def cmd_stats_all(self: DiscordBot, msg: discord.Message, *args: str):
        if msg.author.id != config.admin_user_id:
            status = discord.Embed(title='You must be the bot admin to use this command', color=0x800000)
            await msg.channel.send(None, embed=status)
            return

        cmd_counts = {}
        for cmd in self._cmds:
            if self._cmds[cmd]['perm'] == DiscordCmdBase.ADMINISTRATOR:
                # Don't give stats for admin commands
                continue

            cmd_counts[cmd] = self.db_get_cmd_total_count(cmd)

        cmd_names_txt = '\n'.join(map(str, cmd_counts.keys()))
        cmd_stats_txt = '\n'.join(map(str, cmd_counts.values()))

        reply = discord.Embed(color=0x1abc9c)
        reply.set_author(name='Command Stats')
        reply.add_field(name='', value=f'```{cmd_names_txt}```', inline=True)
        reply.add_field(name='', value=f'```{cmd_stats_txt}```', inline=True)
        reply.set_footer(text='All servers')

        await msg.channel.send(None, embed=reply)


    @DiscordCmdBase.DiscordEvent()
    async def user_engagement_task(self: DiscordBot):
        """
        Data fmt:
            "bot_ch": {
                (server.id: str): { "channel" : (channel.id: int) }
                ...
            }
        """
        logger = logging.getLogger('user_engagement_task')

        while True:
            # Process once a day
            await asyncio.sleep(60*60*24)

            logger.debug(f'tick @ {time.time()}')

            table = self.get_db_table('bot_ch')
            for entry in table:
                guild = self.get_guild(entry.doc_id)
                if isinstance(guild, type(None)):
                    guild = await self.fetch_guild(entry.doc_id)
                    if isinstance(guild, type(None)):
                        continue

                channel = guild.get_channel(entry['channel'])
                if isinstance(channel, type(None)):
                    channel = guild.fetch_channel(entry['channel'])
                    if isinstance(channel, type(None)):
                        continue

                while True:
                    cmd_name, cmd_data = random.choice(list(self._cmds.items()))
                    if cmd_data['perm'] == DiscordCmdBase.ANYONE:
                        break

                embed = discord.Embed(title=f'Did you know :grey_question:', color=0x1B6F5F)
                embed.add_field(
                    name = f'The `{config.cmd_prefix}{cmd_name}` command',
                    value =
                        f'Example: `{cmd_data["example"]}`\n'
                        '```\n'
                        f'{cmd_data["help"]}\n'
                        '```'
                )

                await channel.send(None, embed=embed)

