from typing import Optional

import os
import importlib
import inspect
import traceback
import warnings

import logging
import asyncio
import aiohttp
import tinydb
import threading
import queue

import discord

import config
from main.db_middleware import DbThreadSafeMiddleware

from main.cmds.admin import CmdsAdmin
from main.utils import Utils



class DiscordBot(discord.Client):

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

        discord.Client.__init__(self, intents=intents)
        self.__logger = logging.getLogger(__class__.__name__)
        self.__logger.info('DiscordBot initializing...')

        self._cmds = {}
        self._events = {}
        self._modules = {}

        self.__dbg_ch = None
        self.__curr_msg = {}
        self.__prev_msg = {}

        self.__is_connected = False
        self.__db = tinydb.TinyDB('db.json', storage=DbThreadSafeMiddleware(tinydb.JSONStorage))

        # Needed for misc commands that upload images, downloads, etc
        os.makedirs('cache', exist_ok=True)

        self.__bot_loop = asyncio.get_event_loop()
        self.__bot_loop.create_task(self.start(config.discord_token))

        self.__bot_thread = threading.Thread(target=self.__bot_loop.run_forever)
        self.__bot_thread.setDaemon(True)
        self.__bot_thread.start()


    async def start(self, *args, **kwargs):
        retry = 10

        while True:
            try:
                await self.login(config.discord_token)
            except aiohttp.ClientConnectionError:
                self.__logger.warn(f'Unable to connect to discord. Retrying in {retry} seconds...')

                await asyncio.sleep(retry)
                retry = min(120, retry + 10)

                self.clear()
                continue
            else:
                break

        await self.connect(reconnect=True)


    def get_logger(self):
        if isinstance(self, DiscordBot):
            return self.__logger
    
        return logging.getLogger(type(self))


    async def close(self):
        await discord.Client.close(self)
        config.runtime_quit = True


    async def on_message(self, msg: discord.Message):
        try:
            # TODO: Apply general message stat

            try: self.__prev_msg[msg.channel.id] = self.__curr_msg[msg.channel.id]
            except KeyError:
                pass

            self.__curr_msg[msg.channel.id] = msg

            if msg.author.bot:
                # Don't respond to bots
                return

            if not msg.content.startswith(config.cmd_prefix):
                # Responding to commands only
                return

            if not msg.author.guild_permissions.manage_channels:
                table = self.get_db_table('bot_en')
                if not table.contains(doc_id=msg.channel.id):
                    self.__logger.debug(
                        f'{msg.guild.name}:#{msg.channel.name} @{msg.author.name} | "{config.cmd_prefix}{cmd} {" ".join(args)}"\n'
                        'Ignoring command because channel does not have `bot_en` and user has no manage channel permission.'
                    )
                    return
                else:
                    data = table.get(doc_id=msg.channel.id)
                    if not data['chan_en']:
                        self.__logger.debug(
                            f'{msg.guild.name}:#{msg.channel.name} @{msg.author.name} | "{config.cmd_prefix}{cmd} {" ".join(args)}"\n'
                            'Ignoring command because channel does not have `bot_en` and user has no manage channel permission.'
                        )
                        return

            cmd = msg.content.lstrip(config.cmd_prefix)

            args = cmd.split(' ')
            cmd  = args[0]
            args = args[1:]

            if not cmd in self._cmds:
                self.__logger.debug(f'"{cmd}" invalid cmd')
                return

            self.__bot_loop.create_task(self.__exec_cmd(cmd, msg, args))

            # TODO: Apply command message stat
            self.__logger.debug(f'{cmd}:@{msg.author.name} -> {msg.guild.name}:#{msg.channel.name}')
        except Exception as e:
            self.__logger.error(f'Unable to process `on_message` - {type(e)}: {e}')
            await self.__dbg_ch.send(
                '```\n'
                f'Error: `on_message` crash\n'
                f'Raised {type(e)}: {e}\n\n'
                '```'
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
        bot_dir_files = os.listdir(f'{config.root}/main/cmds')
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
            if channel.id == config.debug_channel:
                self.__dbg_ch = channel

        if isinstance(self.__dbg_ch, type(None)):
            self.__logger.info(f'Debug channel not found!')
        else:
            self.__logger.info(f'Debug channel found!')

        # Run events
        self.__logger.info('Initializing events...')
        for name, event in self._events.items():
            self.__logger.info(f'    {name}')
            self.__bot_loop.create_task(event['func'](self))

        # Present as ready
        self.__logger.info(f'Ready!')
        await self.change_presence(activity=discord.Game(':bat:'), status=discord.Status.online)


    def get_prev_msg(self, channel_id: int) -> Optional[discord.Message]:
        try: return self.__prev_msg[channel_id]
        except KeyError:
            return None


    def get_db_table(self, table: str) -> tinydb.TinyDB.table_class:
        return self.__db.table(table)


    async def run_help_cmd(self: "DiscordBot", msg: discord.Message, cmd: str):
        await self._cmds['help']['func'](self, msg, cmd)


    async def __main_loop(self):
        self.__logger.info('Running main loop...')

        while True:
            await asyncio.sleep(1)
            
            if config.runtime_quit:
                await self.__report('Exiting discord loop...')
                await self.close()
                return

            if not self.__is_connected:
                continue


    async def __exec_cmd(self, cmd: str, msg: discord.Message, args: list):
        with warnings.catch_warnings(record=True) as w:
            try: await self._cmds[cmd]['func'](self, msg, *args)
            except Exception as e:
                err = Utils.format_exception(e)

                await self.__report(
                    f'[ ERROR ]\n'
                    f'{msg.guild.name}:#{msg.channel.name} @{msg.author.name} | "{config.cmd_prefix}{cmd} {" ".join(args)}"\n'
                    f'{err}\n'
                )

            # Process warnings
            for warning in w:
                file = warning.filename.split('\\')[-1]
                err = f'  {file}, line {warning.lineno}'

                await self.__report(
                    f'[ WARNING ]\n'
                    f'{msg.guild.name}:#{msg.channel.name} @{msg.author.name} | "{config.cmd_prefix}{cmd} {" ".join(args)}"\n'
                    f'Warning: {warning.message}\n'
                    f'{err}\n'
                )

            w.clear()


    async def __report(self, msg: str, log: bool = True):
        if log:
            self.__logger.warn(msg)

        if self.__dbg_ch is None:
            self.__logger.warn(
                f'Enable to send message to debug channel - Does channel exist?\n'
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
