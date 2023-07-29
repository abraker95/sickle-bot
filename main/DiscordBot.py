from typing import Optional

import os
import importlib
import inspect
import warnings
import time

import logging
import asyncio
import aiohttp
import threading

import discord
import git
import yaml

import tinydb
from tinydb.table import Document
from main.db_middleware import DbThreadSafeMiddleware

from main.utils import Utils



class DiscordBot(discord.Client):

    __MSG_TYPE_TOTAL = 0
    __MSG_TYPE_USERS = 1
    __MSG_TYPE_CMDS  = 2

    __DB_BOT_CFG_INFO_MSG = 0

    with open('config.yaml', 'r') as f:
        CONFIG = yaml.safe_load(f)

    cmd_prefix = CONFIG['Core']['cmd_prefix']

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

        discord.Client.__init__(self, intents=intents)

        self.__logger = logging.getLogger(__class__.__name__)
        self.__logger.info('DiscordBot initializing...')

        self.quit     = False
        self._cfg     = {}

        self._cmds    = {}
        self._events  = {}
        self._modules = {}

        self.__dbg_ch = None
        self.__curr_msg = {}
        self.__prev_msg = {}

        self.__is_connected = False
        self.__db = tinydb.TinyDB('db.json', storage=DbThreadSafeMiddleware(tinydb.JSONStorage))

        # Needed for misc commands that upload images, downloads, etc
        os.makedirs('cache', exist_ok=True)

        self.__bot_loop = asyncio.get_event_loop()
        self.__bot_loop.create_task(self.start(self.get_cfg('Core', 'discord_token')))

        self.__bot_thread = threading.Thread(target=self.__bot_loop.run_forever)
        self.__bot_thread.setDaemon(True)
        self.__bot_thread.start()


    async def start(self, *args, **kwargs):
        retry = 10

        while True:
            try:
                await self.login(self.get_cfg('Core', 'discord_token'))
            except aiohttp.ClientConnectionError as e:
                self.__logger.warn(f'Unable to connect to discord; {e}. Retrying in {retry} seconds...')

                await asyncio.sleep(retry)
                retry = min(120, retry + 10)

                self.clear()
                continue
            except KeyboardInterrupt:
                self.close()
                return
            else:
                break

        await self.connect(reconnect=True)


    def get_logger(self):
        if isinstance(self, DiscordBot):
            return self.__logger

        return logging.getLogger(type(self))


    async def close(self):
        await discord.Client.close(self)
        self.quit = True


    async def on_message(self, msg: discord.Message):
        try:
            if isinstance(msg.guild, type(None)):
                await self.__handle_dm_msg(msg)
                return

            if msg.channel.id == self.__dbg_ch.id:
                await self.__handle_dev_ch_msg(msg)
                return

            await self.__handle_server_msg(msg)
        except Exception as e:
            await self.__report(
                f'Error: `on_message` crash\n'
                f'{Utils.format_exception(e)}'
            )


    async def on_disconnect(self):
        if not self.__is_connected:
            return

        self.__is_connected = False
        self.__logger.warn(f'Diconnected from discord!')


    async def on_connect(self):
        if self.__is_connected:
            return

        self.__is_connected = True
        self.__logger.info(f'Connected to discord!')
        self.__logger.info(f'Serving {len(self.guilds)} servers')


    async def setup_hook(self):
        self.__logger.info(f'Registering commands and creating tasks...')

        # Create main loop
        self.loop.create_task(self.__main_loop())

        # Load commands
        root = os.path.abspath(os.path.dirname(__file__))
        bot_dir_files = os.listdir(f'{root}/cmds')
        self.__logger.debug(f'Files found: {bot_dir_files}')

        module_files = [ f[:-3] for f in bot_dir_files if f != '__init__.py' and f[-3:] == '.py' ]
        self.__logger.debug(f'Modules found: {module_files}')

        for module_file in module_files:
            self.__logger.info(f'Importing {module_file}')

            try: module = importlib.import_module(f'main.cmds.{module_file}')
            except Exception as e:
                self.__logger.error(f'   error importing: {e}')
                continue

            self._modules[module_file] = []

            # Convert from snake_case to CamelCase
            class_name = f'Cmds{"".join([ (word[0].upper() + word[1:]) for word in module_file.split("_") ])}'

            class_type = getattr(module, class_name)
            members = inspect.getmembers(class_type)

            for name, member in members:
                if isinstance(member, dict):
                    if not 'func'    in member: continue
                    if not 'example' in member: continue
                    if not 'type'    in member: continue
                    if not 'help'    in member: continue

                    # Underscores '_' in command names don't look nice
                    # Replace them with period '.'
                    name = name.replace('_', '.')

                    self.__logger.info(f'    {name}')

                    if member['type'] == 'cmd':
                        self._cmds[name] = member
                        self._modules[module_file].append(name)

                    if member['type'] == 'event':
                        self._events[name] = member

                    continue

                if not inspect.isfunction(member):
                    continue

                if not name in self._cmds:
                    if f'_{class_name}__' in name:
                        # It's a private function, skip
                        continue

                    self.__logger.warning(f'"{name}" command will not be added. This warning can be ignored if this is intentional.')

                self.__logger.warning(f'"{name}" command is not wrapped in `DiscordCmdBase.DiscordCmd`. "help" cmd usage info will be unavailable!')

                self.__logger.info(f'    {name}')
                self._cmds[name]['fn']      = member
                self._cmds[name]['example'] = ''
                self._cmds[name]['help']    = ''
                self._modules[module_file].append(name)


    async def on_ready(self):
        await self.wait_until_ready()

        # Look for debug channel where errors would get posted
        self.__logger.info(f'Looking for debug channel...')
        self.__dbg_ch = None

        for channel in self.get_all_channels():
            if channel.id == self.get_cfg('Core', 'debug_channel'):
                self.__dbg_ch = channel

            # Auto assign bot channel if not set and enable it in there
            if 'bot' in channel.name:
                table = self.get_db_table('bot_ch')
                if not table.contains(doc_id=channel.guild.id):
                    self.__logger.info(f'Setting bot channel for {channel.guild.name}#{channel.name} | {channel.guild.id}.{channel.id}')
                    table.insert(Document({ 'channel' : channel.id }, channel.guild.id))

                table = self.get_db_table('bot_en')
                if not table.contains(doc_id=channel.id):
                    table.insert(Document({ 'chan_en' : True }, channel.id))

        if isinstance(self.__dbg_ch, type(None)):
            self.__logger.info(f'Debug channel not found!')
        else:
            self.__logger.info(f'Debug channel found!')

        # Run events
        self.__logger.info('Initializing events...')
        for name, event in self._events.items():
            if event['en']:
                self.__logger.info(f'    {name}')
                self.__bot_loop.create_task(event['func'](self))

        # Present as ready
        self.__logger.info(f'Ready!')
        await self.change_presence(activity=discord.Game(':bat:'), status=discord.Status.online)
        await self.__report('Discord loop started')


    @staticmethod
    def get_cfg(src: str, key: str):
        try: return DiscordBot.CONFIG[src][key]
        except KeyError as e:
           raise KeyError(f'Config get failure: {src}.{key}') from e


    def get_prev_msg(self, channel_id: int) -> Optional[discord.Message]:
        try: return self.__prev_msg[channel_id]
        except KeyError:
            return None


    def get_db_table(self, table: str) -> tinydb.TinyDB.table_class:
        return self.__db.table(table)


    async def run_help_cmd(self: "DiscordBot", msg: discord.Message, cmd: str):
        await self._cmds['help']['func'](self, msg, cmd)


    async def __handle_dm_msg(self, msg: discord.Message):
        if msg.author.bot:
            # Don't respond to bots
            return

        if msg.reference:
            ref_msg = await msg.channel.fetch_message(msg.reference.message_id)
            if ref_msg.author.id != self.user.id:
                return

            # Message the devs if the user replies to the bot
            ref_content = \
            ''.join(
                f'{line}\n'
                for line in ref_msg.content.split('\n')
            ) + \
            ''.join([
                f'{line}\n'
                for embed in ref_msg.embeds
                for field in embed.fields
                for line in field.value.split('\n')
            ]) + \
            '===================\n' + \
            msg.content

            await self.msg_dev(msg, f'{ref_content}\n')
            return

        if not msg.content.startswith(self.cmd_prefix):
            await msg.channel.send(self.db_get_info_msg())
            return

        cmd = msg.content.lstrip(self.cmd_prefix)

        args = cmd.split(' ')
        cmd  = args[0]
        args = args[1:]

        if not cmd in self._cmds:
            self.__logger.debug(f'"{cmd}" invalid cmd')
            return

        self.__bot_loop.create_task(self.__exec_cmd(cmd, msg, args))
        self.__logger.debug(f'{cmd}:@{msg.author.name} -> DM')


    async def __handle_server_msg(self, msg: discord.Message):
        try: self.__prev_msg[msg.channel.id] = self.__curr_msg[msg.channel.id]
        except KeyError:
            pass

        self.__curr_msg[msg.channel.id] = msg
        self.__db_inc_msgs(msg, DiscordBot.__MSG_TYPE_TOTAL)

        if msg.author.bot:
            # Don't respond to bots
            return

        self.__db_inc_msgs(msg, DiscordBot.__MSG_TYPE_USERS)

        if msg.reference:
            try: ref_msg = await msg.channel.fetch_message(msg.reference.message_id)
            except discord.NotFound:
                await self.__report(
                    f'[ WARNING ]\n'
                    'Failed fetch reply to message\n'
                    '-------------------------------'
                    f'User:    {msg.author} ({msg.author.id})'
                    f'Server:  {msg.guild.name} ({msg.guild.id}) -> ({msg.reference.guild_id})'
                    f'Channel: {msg.channel.name} ({msg.channel.id}) -> ({msg.channel.category_id})'
                    f'Message: {msg.id} -> {msg.reference.message_id}'
                    f'Url:     {msg.jump_url} -> {msg.reference.jump_url}'
                )

                # TODO: Check if the bot have access to the channel
                return

            if ref_msg.author.id != self.user.id:
                return

            # Message the devs if the user replies to the bot
            ref_content = \
            ''.join(
                f'{line}\n'
                for line in ref_msg.content.split('\n')
            ) + \
            ''.join([
                f'{line}\n'
                for embed in ref_msg.embeds
                for field in embed.fields
                for line in field.value.split('\n')
            ]) + \
            '===================\n' + \
            msg.content

            await self.msg_dev(msg, f'{ref_content}\n')
            return

        if not msg.content.startswith(self.cmd_prefix):
            # Responding to commands only
            return

        self.__db_inc_msgs(msg, DiscordBot.__MSG_TYPE_CMDS)

        cmd = msg.content.lstrip(self.cmd_prefix)

        args = cmd.split(' ')
        cmd  = args[0]
        args = args[1:]

        if not msg.author.guild_permissions.manage_channels:
            if not self._cmds['anywhere']:
                table = self.get_db_table('bot_en')
                if not table.contains(doc_id=msg.channel.id):
                    self.__logger.debug(
                        f'{msg.guild.name}:#{msg.channel.name} @{msg.author.name} | "{self.cmd_prefix}{cmd} {" ".join(args)}"\n'
                        'Ignoring command because channel does not have `bot_en` and user has no manage channel permission.'
                    )
                    return
                else:
                    data = table.get(doc_id=msg.channel.id)
                    if not data['chan_en']:
                        self.__logger.debug(
                            f'{msg.guild.name}:#{msg.channel.name} @{msg.author.name} | "{self.cmd_prefix}{cmd} {" ".join(args)}"\n'
                            'Ignoring command because channel does not have `chan_en` and user has no manage channel permission.'
                        )
                        return

        if not cmd in self._cmds:
            self.__logger.debug(f'"{cmd}" invalid cmd')
            return

        self.__bot_loop.create_task(self.__exec_cmd(cmd, msg, args))
        self.__logger.debug(f'{cmd}:@{msg.author.name} -> {msg.guild.name}:#{msg.channel.name}')

        self.__db_inc_cmd_count(msg.guild.id, cmd)


    async def __handle_dev_ch_msg(self, msg: discord.Message):
        if msg.author.bot:
            # Don't respond to bots
            return

        if msg.reference:
            ref_msg = await msg.channel.fetch_message(msg.reference.message_id)
            if ref_msg.author.id != self.user.id:
                return

            # Message back the user if the dev replies to the bot
            # Resolve channel ID
            try:
                footer_text = ref_msg.embeds[0]._footer['text']
                source_ids = ref_msg.embeds[0]._footer['text'].split('|')[1].split('.')
            except IndexError:
                await self.__report(
                    f'[ WARNING ]\n'
                    'Replied to wrong message probably\n'
                )
                return

            if 'DM' in footer_text:
                source_user_id = int(source_ids[0].strip())
                source_ch_id   = int(source_ids[1].strip())
                source_msg_id  = int(source_ids[2].strip())
            else:
                source_user_id = None
                source_ch_id   = int(source_ids[1].strip())
                source_msg_id  = int(source_ids[2].strip())

            try: source_ch = await self.fetch_channel(source_ch_id)
            except discord.NotFound:
                await self.__report(
                    f'[ WARNING ]\n'
                    'Failed to reply to message: Cannot fetch channel\n'
                )
                return

            try: source_msg = await source_ch.fetch_message(source_msg_id)
            except discord.NotFound:
                await self.__report(
                    f'[ WARNING ]\n'
                    'Failed to reply to message: Cannot fetch message\n'
                )
                return

            content = \
            ''.join(
                f'{line}\n'
                for line in ref_msg.content.split('\n')
            ) + \
            ''.join([
                f'{line}\n'
                for embed in ref_msg.embeds
                for field in embed.fields
                for line in field.value.split('\n')
            ]) + \
            '===================\n' + \
            msg.content

            await self.reply_msg(source_msg, content)
            return

        if not msg.content.startswith(self.get_cfg('Core', 'cmd_prefix')):
            return

        cmd = msg.content.lstrip(self.get_cfg('Core', 'cmd_prefix'))

        args = cmd.split(' ')
        cmd  = args[0]
        args = args[1:]

        if not cmd in self._cmds:
            self.__logger.debug(f'"{cmd}" invalid cmd')
            return

        self.__bot_loop.create_task(self.__exec_cmd(cmd, msg, args))
        self.__logger.debug(f'{cmd}:@{msg.author.name} -> DM')


    async def __main_loop(self):
        self.__logger.info('Running main loop...')

        while True:
            await asyncio.sleep(1)

            if self.quit:
                await self.__report('Exiting discord loop...')
                await self.close()
                return

            if not self.__is_connected:
                continue


    async def __exec_cmd(self, cmd: str, msg: discord.Message, args: list):
        with warnings.catch_warnings(record=True) as w:
            try: await self._cmds[cmd]['func'](self, msg, *args)
            except Exception as e:
                try:
                    embed = discord.Embed(type='rich', color=0xFF9900, title='⚠ Error')
                    embed.add_field(name='Something went wrong', value=f'Do not panic! The developers have been notified.')
                    await msg.channel.send(None, embed=embed)
                except Exception:
                    pass

                err = Utils.format_exception(e)

                try: server_name = msg.guild.name
                except AttributeError:
                    server_name = 'DM'

                try: channel_name = msg.channel.name
                except AttributeError:
                    channel_name = ''

                await self.__report(
                    f'[ ERROR ]\n'
                    f'{server_name}:#{channel_name} @{msg.author.name} | "{self.cmd_prefix}{cmd} {" ".join(args)}"\n'
                    f'{err}\n'
                )

            # Process warnings
            for warning in w:
                file = warning.filename.split('\\')[-1]
                err = f'  {file}, line {warning.lineno}'

                try: server_name = msg.guild.name
                except AttributeError:
                    server_name = 'DM'

                try: channel_name = msg.channel.name
                except AttributeError:
                    channel_name = ''

                await self.__report(
                    f'[ WARNING ]\n'
                    f'{server_name}:#{channel_name} @{msg.author.name} | "{self.cmd_prefix}{cmd} {" ".join(args)}"\n'
                    f'Warning: {warning.message}\n'
                    f'{err}\n'
                )

            w.clear()


    async def __report(self, msg: str, log: bool = True):
        if log:
            self.__logger.warn(msg)

        if self.__dbg_ch is None:
            self.__logger.warn(
                f'Unable to send message to debug channel - Does channel exist?\n'
                f'Msg:\n'
                f'    {msg}\n'
            )
            return

        try: await self.__dbg_ch.send(
            '```\n'
            # Sanitize backticks
            f'{msg.replace("```", "`​`​`")}'
            '```'
        )
        except discord.errors.HTTPException as e:
            self.__logger.warn(f'Unable to send message to debug channel | HTTP Exception - {e}')
            if e.status == 400:  # HTTP Bad request
                # Still attempt to notify
                await self.__dbg_ch.send(
                    '```\n'
                    f'Warning: Attempted to send malformed message. Error contents will be available in logs\n'
                    '```'
                )
        except RuntimeError as e:
            self.__logger.warn(
                f'Unable to send message to debug channel | {e}\n'
                f'Msg:\n'
                f'    {msg}\n'
            )


    async def reply_msg(self, msg: discord.Message, content: str):
        content = f'{content.replace("```", "`​`​`")}'

        embed = discord.Embed(color=0x0099FF)
        embed.add_field(name='dev reply', value=content)
        await msg.reply(None, embed=embed)


    async def msg_dev(self, msg: discord.Message, content: str):
        content = f'{content.replace("```", "`​`​`")}'

        if isinstance(msg.guild, type(None)):
            server_text = f'From DM | {msg.author.id}.{msg.channel.id}.{msg.id}'
        else:
            try:
                invites = await msg.guild.invites()
                server_text = f'From [{msg.guild.name}]#[{msg.channel.name}] ({invites[0]}) | {msg.guild.id}.{msg.channel.id}.{msg.id}'
            except:
                server_text = f'From [{msg.guild.name}]#[{msg.channel.name}] | {msg.guild.id}.{msg.channel.id}.{msg.id}'

        print(server_text)

        embed = discord.Embed(color=0x0099FF)
        embed.add_field(name=f'{msg.author.name} (id: {msg.author.id})', value=content)
        embed.set_thumbnail(url=msg.author.avatar.url)
        embed.set_footer(text=server_text)
        await self.__dbg_ch.send(None, embed=embed)


    def get_version(self) -> str:
        try: repo = git.Repo('.')
        except git.NoSuchPathError:
            return 'v?'

        date = repo.head.commit.committed_date
        return time.strftime('v%Y.%m.%d', time.gmtime(date))


    def __db_inc_msgs(self, msg: discord.Message, msg_type: int):
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
        if isinstance(msg.guild, type(None)):
            # Probably private DM
            return

        table = self.get_db_table('bot_stats')
        entry = table.get(doc_id=msg.guild.id)

        if isinstance(entry, type(None)):
            data = {
                'total_msgs' : 1 if msg_type == DiscordBot.__MSG_TYPE_TOTAL else 0,
                'user_msgs'  : 1 if msg_type == DiscordBot.__MSG_TYPE_USERS else 0,
                'total_cmds' : 1 if msg_type == DiscordBot.__MSG_TYPE_CMDS  else 0,
            }
            table.insert(Document(data, doc_id=msg.guild.id))
            return

        if msg_type == DiscordBot.__MSG_TYPE_TOTAL: entry['total_msgs'] += 1
        if msg_type == DiscordBot.__MSG_TYPE_USERS: entry['user_msgs'] += 1
        if msg_type == DiscordBot.__MSG_TYPE_CMDS:  entry['total_cmds'] += 1

        table.update(entry)


    def __db_inc_cmd_count(self, server_id: int, cmd: str):
        """
        Data fmt:
            "cmd_stats": {
                (doc_id: int) : { 'cmd' : (cmd: str), 'server' : (server_id: int), 'count' : (count: int) },
                (doc_id: int) : { 'cmd' : (cmd: str), 'server' : (server_id: int), 'count' : (count: int) },
                ...
            }
        """
        table = self.get_db_table('cmd_stats')
        entry = table.get(tinydb.Query().fragment({'cmd' : cmd, 'server' : server_id}))

        if not entry:
            table.insert({ 'cmd' : cmd, 'server' : server_id, 'count' : 1 })
        else:
            table.update({ 'count' : entry['count'] + 1 }, doc_ids=[ entry.doc_id ])


    def db_get_cmd_server_count(self, server_id: int, cmd: str) -> int:
        """
        Data fmt:
            "cmd_stats": {
                (doc_id: int) : { 'cmd' : (cmd: str), 'server' : (server_id: int), 'count' : (count: int) },
                (doc_id: int) : { 'cmd' : (cmd: str), 'server' : (server_id: int), 'count' : (count: int) },
                ...
            }
        """
        table = self.get_db_table('cmd_stats')
        entry = table.get(tinydb.Query().fragment({'cmd' : cmd, 'server' : server_id}))
        return 0 if not entry else entry['count']


    def db_get_cmd_total_count(self, cmd: str) -> int:
        """
        Data fmt:
            "cmd_stats": {
                (doc_id: int) : { 'cmd' : (cmd: str), 'server' : (server_id: int), 'count' : (count: int) },
                (doc_id: int) : { 'cmd' : (cmd: str), 'server' : (server_id: int), 'count' : (count: int) },
                ...
            }
        """
        table = self.get_db_table('cmd_stats')
        entries = table.search(tinydb.Query().fragment({'cmd' : cmd}))
        return sum([ entry['count'] for entry in entries ])


    def db_set_info_msg(self, msg: str):
        """
        Data fmt:
            "bot_cfg": {
                (doc_id: 0) : {
                    'info' : (msg: str)
                }
            }
        """
        table = self.get_db_table('bot_cfg')
        entry = table.get(doc_id=DiscordBot.__DB_BOT_CFG_INFO_MSG)

        if not entry:
            table.insert({ 'info' : msg })
        else:
            table.update({ 'info' : msg }, doc_ids=[ DiscordBot.__DB_BOT_CFG_INFO_MSG ])


    def db_get_info_msg(self) -> str:
        """
        Data fmt:
            "bot_cfg": {
                (doc_id: 0) : {
                    'info' : (msg: str)
                }
            }
        """
        table = self.get_db_table('bot_cfg')
        entry = table.get(doc_id=DiscordBot.__DB_BOT_CFG_INFO_MSG)

        if not entry:
            return 'Use ">>devs {msg}" to notify devs of any issues'

        return entry['info']
