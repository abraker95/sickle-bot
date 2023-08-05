import discord

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
        example = f'{DiscordBot.cmd_prefix}kill',
        help    =
            'Forcefully kill the bot.'
    )
    async def kill(self: DiscordBot, msg: discord.Message, *args: "list[str]"):
        if msg.author.id != DiscordBot.get_cfg('Core', 'admin_user_id'):
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
                feed_server_port = DiscordBot.get_cfg('Core', 'feed_server_port')
                async with session.put(f'http://127.0.0.1:{feed_server_port}/internal', timeout=1, json=data) as response:
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
        example = f'{DiscordBot.cmd_prefix}feed.ping',
        help    =
            'Pings the feed server.'
    )
    async def feed_ping(self: DiscordBot, msg: discord.Message, *args: "list[str]"):
        if msg.author.id != DiscordBot.get_cfg('Core', 'admin_user_id'):
            status = discord.Embed(title='You must be the bot admin to use this command', color=0x800000)
            await msg.channel.send(None, embed=status)
            return

        async with aiohttp.ClientSession() as session:
            try:
                feed_server_port = DiscordBot.get_cfg('Core', 'feed_server_port')
                async with session.put(f'http://127.0.0.1:{feed_server_port}/ping', timeout=1) as response:
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
        example = f'{DiscordBot.cmd_prefix}eval print("hello world")',
        help    =
            'Executes raw python code. This should be used with caution.'
    )
    async def eval(self: DiscordBot, msg: discord.Message, *args: "list[str]"):
        if msg.author.id != DiscordBot.get_cfg('Core', 'admin_user_id'):
            status = discord.Embed(title='You must be the bot admin to use this command', color=0x800000)
            await msg.channel.send(None, embed=status)
            return

        if len(args) == 0:
            await self.run_help_cmd(msg, 'eval')
            return

        code = ' '.join(args)
        code = code.replace('```', '')

        output = eval(code)
        if inspect.isawaitable(output):
            output = await output

        output = str(output)

        if not output:
            status = discord.Embed(title='✅ Executed', color=0x66CC66)
            await msg.channel.send(None, embed=status)
            return

        for i in range(0, len(output), 1000):
            status = discord.Embed(color=0x66CC66)
            status.add_field(name='Results', value=f'\n```\n{output[i : i + 1000]}\n```')
            await msg.channel.send(None, embed=status)


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        perm    = DiscordCmdBase.ADMINISTRATOR,
        example = f'{DiscordBot.cmd_prefix}bot.stats',
        help    =
            'Prints this bots\'s stats'
    )
    async def bot_stats(self: DiscordBot, msg: discord.Message, *args: "list[str]"):
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
        if msg.author.id != DiscordBot.get_cfg('Core', 'admin_user_id'):
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
        example = f'{DiscordBot.cmd_prefix}cmd.stats.all',
        help    =
            'Prints command usage stats for all servers'
    )
    async def cmd_stats_all(self: DiscordBot, msg: discord.Message, *args: "list[str]"):
        if msg.author.id != DiscordBot.get_cfg('Core', 'admin_user_id'):
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


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        perm    = DiscordCmdBase.ADMINISTRATOR,
        example = f'{DiscordBot.cmd_prefix}cmd.set.info',
        help    =
            'Info message that gets printed when a user responds to the bot in DMs'
    )
    async def cmd_set_info(self: DiscordBot, msg: discord.Message, *args: "list[str]"):
        if msg.author.id != DiscordBot.get_cfg('Core', 'admin_user_id'):
            status = discord.Embed(title='You must be the bot admin to use this command', color=0x800000)
            await msg.channel.send(None, embed=status)
            return

        self.db_set_info_msg(' '.join(args))

        status = discord.Embed(title='✅ Info message set', color=0x66CC66)
        await msg.channel.send(None, embed=status)


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        perm    = DiscordCmdBase.ADMINISTRATOR,
        example = f'{DiscordBot.cmd_prefix}bot.set.dbg',
        help    =
            'Toggles debug logs into dev channel'
    )
    async def bot_set_dbg(self: DiscordBot, msg: discord.Message, *args: "list[str]"):
        if msg.author.id != DiscordBot.get_cfg('Core', 'admin_user_id'):
            status = discord.Embed(title='You must be the bot admin to use this command', color=0x800000)
            await msg.channel.send(None, embed=status)
            return

        self.is_debug = not self.is_debug

        status = discord.Embed(title=f'✅ Debug {"enabled" if self.is_debug else "disabled"}', color=0x66CC66)
        await msg.channel.send(None, embed=status)


    @DiscordCmdBase.DiscordEvent(en = False)
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
                    name = f'The `{DiscordBot.cmd_prefix}{cmd_name}` command',
                    value =
                        f'Example: `{cmd_data["example"]}`\n'
                        '```\n'
                        f'{cmd_data["help"]}\n'
                        '```'
                )

                await channel.send(None, embed=embed)

            # TODO: Once a day at a random time, where enabled, if nobody used the bot in the last 72h,
            # pick a common user command and post a "did you know you can use this" type of post
            #
            # Maybe have a probalistic determined point of posting:
            #   - Odds of posting at any given hour
            #   - Odds of posting soon after someone used the bot approach 0%
            #   - Odds increase starting the following day and level off at 1/N
            #   - If nobody uses the bot, expect to post once every 3-7 days
