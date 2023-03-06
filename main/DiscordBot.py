import os
import importlib
import inspect

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



class DiscordBot(discord.Client):

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

        discord.Client.__init__(self, intents=intents)
        self.__logger = logging.getLogger(__class__.__name__)
        self.__logger.info('DiscordBot initializing...')       

        self.__is_connected = False
        self.__queue = queue.Queue()
        self.__cmds = {}
        self.__db = tinydb.TinyDB('db.json', storage=DbThreadSafeMiddleware(tinydb.JSONStorage))

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


    async def close(self):
        await discord.Client.close(self)
        config.runtime_quit = True


    async def on_message(self, msg : discord.Message):
        # TODO: Apply general message stat

        if msg.author.bot:
            # Don't respond to bots
            return

        if not msg.content.startswith(config.cmd_prefix):
            # Responding to commands only
            return

        cmd = msg.content.lstrip(config.cmd_prefix)
        if not cmd in self.__cmds:
            # Invalid command
            return

        self.__bot_loop.create_task(self.__cmds[cmd](self, msg))

        # TODO: Apply command message stat
        self.__logger.debug(msg)


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
        self.loop.create_task(self.__main_loop())

        # Load commands
        bot_dir_files = os.listdir(f'{config.root}/main/cmds')
        self.__logger.debug(f'Files found: {bot_dir_files}')

        module_files = [ f[:-3] for f in bot_dir_files if f != '__init__.py' and f[-3:] == '.py' ]
        self.__logger.debug(f'Modules found: {module_files}')

        for module_file in module_files:
            self.__logger.info(f'Importing {module_file}')
            module = importlib.import_module(f'main.cmds.{module_file}')

            # Convert from snake_case to CamelCase
            class_name = f'Cmds{"".join([ (word[0].upper() + word[1:]) for word in module_file.split("_") ])}'

            class_type = getattr(module, class_name)
            members = inspect.getmembers(class_type)

            for name, member in members:
                if not inspect.isfunction(member):
                    continue

                self.__logger.debug(f'Adding command: {name}')
                self.__cmds[name] = member


    async def on_ready(self):
        await self.wait_until_ready()
        self.__logger.info(f'Ready!')

        await self.change_presence(activity=discord.Game(':bat:'), status=discord.Status.online)


    def queue_data(self, data):
        self.__queue.put(data)


    async def __main_loop(self):
        self.__logger.info('Running main loop...')

        while True:
            await asyncio.sleep(1)
            
            if config.runtime_quit:
                self.__logger.info('Exiting discord loop...')
                await self.__report_error('Exiting discord loop...', log=False)
                await self.close()
                return

            if not self.__is_connected:
                continue


    async def __report_error(self, msg, log=True):
        if log:
            self.__logger.warn(msg)

        debug_channel = None

        # for channel in self.server.channels:
        #     if channel.id == config.debug_channel:
        #         debug_channel = channel

        if debug_channel is None:
            self.__logger.warn(f'Enable to send error message to debug channel - Does channel exist?')
            return

        try: await debug_channel.send(msg)
        except discord.errors.HTTPException as e:
            self.__logger.warn(f'Enable to send error message to debug channel - HTTP Exception')
