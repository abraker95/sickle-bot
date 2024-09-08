import discord
import warnings
import logging

from tinydb.table import Document

from core import DiscordCmdBase, DiscordBot


class CmdsModeration:

    @staticmethod
    async def __custom_command(self: DiscordBot, msg: discord.Message, cmd_server_id: int, cmd_txt: str):
        if msg.guild.id != cmd_server_id:
            pass

        await msg.channel.send(cmd_txt)


    @DiscordCmdBase.DiscordCmd(
        perm    = DiscordCmdBase.MODERATOR,
        example = f'{DiscordBot.cmd_prefix}bot.en true',
        help    =
            'Enable/Disable the bot in the channel.'
    )
    async def bot_en(self: DiscordBot, msg: discord.Message, *args: "list[str]"):
        """
        Data fmt:
            "bot_en": {
                (msg.channel.id: str): {
                    "chan_en": (en: bool)
                },
                ...
            }
        """
        if not msg.author.guild_permissions.manage_channels:
            embed = discord.Embed(type='rich', color=0xFF9900, title='⚠ Error')
            embed.add_field(name='Insufficient permissions', value=f'You need the manage channel permission to use this command')
            await msg.channel.send(None, embed=embed)

        if len(args) != 1:
            await self.run_help_cmd(msg, 'bot.en')
            return

        if   args[0].lower() == 'true':  en = True
        elif args[0].lower() == 'false': en = False
        else:
            await self.run_help_cmd(msg, 'bot.en')
            return

        table = self.db.table('bot_en')
        if not table.contains(doc_id=msg.channel.id):
            table.insert(Document({ 'chan_en' : en }, msg.channel.id))
        else:
            table.upsert(Document({ 'chan_en' : en }, msg.channel.id))

        en_text = 'Enabled' if en else 'Disabled'

        embed = discord.Embed(title=f'{en_text} bot in #{msg.channel.name}', color=0x1ABC9C)
        await msg.channel.send(None, embed=embed)


    @DiscordCmdBase.DiscordCmd(
        perm    = DiscordCmdBase.MODERATOR,
        example = f'{DiscordBot.cmd_prefix}bot.set.ch',
        help    =
            'Set this channel to be THE bot channel. Or use it in this channel again to undo.'
    )
    async def bot_set_ch(self: DiscordBot, msg: discord.Message, *args: "list[str]"):
        """
        Data fmt:
            "bot_ch": {
                (server.id: str): { "channel" : (channel.id: int) }
                ...
            }
        """
        if not msg.author.guild_permissions.manage_channels:
            embed = discord.Embed(type='rich', color=0xFF9900, title='⚠ Error')
            embed.add_field(name='Insufficient permissions', value=f'You need the manage channel permission to use this command')
            await msg.channel.send(None, embed=embed)

        table = self.db.table('bot_ch')
        if not table.contains(doc_id=msg.guild.id):
            table.insert(Document({ 'channel' : msg.channel.id }, msg.guild.id))

            embed = discord.Embed(title=f'Set #{msg.channel.name} to be the bot channel', color=0x1ABC9C)
            await msg.channel.send(None, embed=embed)
            return

        entry = table.get(doc_id=msg.guild.id)
        if isinstance(entry, type(None)):
            warnings.warn('Got none result despite having an entry')
            raise Exception

        if entry['channel'] != msg.channel.id:
            table.upsert(Document({ 'channel' : msg.channel.id }, msg.guild.id))

            embed = discord.Embed(title=f'Set #{msg.channel.name} to be the bot channel', color=0x1ABC9C)
            await msg.channel.send(None, embed=embed)
            return

        table.remove(None, doc_ids=[ msg.guild.id ])

        embed = discord.Embed(title=f'Set #{msg.channel.name} to no longer be the bot channel', color=0x1ABC9C)
        await msg.channel.send(None, embed=embed)


    @DiscordCmdBase.DiscordCmd(
        perm    = DiscordCmdBase.ANYONE,
        example = f'{DiscordBot.cmd_prefix}bot.get.ch',
        help    =
            'Displays currently set bot channel (if there is one).'
    )
    async def bot_get_ch(self: DiscordBot, msg: discord.Message, *args: "list[str]"):
        """
        Data fmt:
            "bot_ch": {
                (server.id: str): { "channel" : (channel.id: int) }
                ...
            }
        """
        table = self.db.table('bot_ch')
        if not table.contains(doc_id=msg.guild.id):
            embed = discord.Embed(title=f'No bot channel set', color=0x1ABC9C)
            await msg.channel.send(None, embed=embed)
            return

        entry = table.get(doc_id=msg.guild.id)
        if isinstance(entry, type(None)):
            warnings.warn('Got none result despite having an entry')
            raise Exception

        channel = msg.guild.get_channel(entry['channel'])
        if isinstance(channel, type(None)):
            channel = await msg.guild.fetch_channel(entry['channel'])
            if isinstance(channel, type(None)):
                embed = discord.Embed(title=f'Bot channel no longer exists. Consider getting a moderator to update the bot channel setting.', color=0x1ABC9C)
                await msg.channel.send(None, embed=embed)
                return

        embed = discord.Embed(title=f'Bot channel: #{channel.name}', color=0x1ABC9C)
        await msg.channel.send(None, embed=embed)
        return


    @DiscordCmdBase.DiscordCmd(
        perm     = DiscordCmdBase.MODERATOR,
        example  = f'{DiscordBot.cmd_prefix}bot.cmd.set [cmd] [text]',
        help     =
            'Add a custom command that messages the chat.'
    )
    async def bot_cmd_set(self: DiscordBot, msg: discord.Message, *args: "list[str]"):
        """
        Data fmt:
            "custom_cmds": {
                (server.id: str): {
                    (cmd: str) : (msg: str),
                    (cmd: str) : (msg: str),
                    ...
                },
                ...
            }
        """
        if not msg.author.guild_permissions.manage_channels:
            embed = discord.Embed(type='rich', color=0xFF9900, title='⚠ Error')
            embed.add_field(name='Insufficient permissions', value=f'You need the manage channel permission to use this command')
            await msg.channel.send(None, embed=embed)

        if len(args) < 2:
            await self.run_help_cmd(msg, 'bot.cmd.set')
            return

        cmd_txt = args[0]
        cmd_msg = ' '.join(args[1:])

        for module in self._modules.values():
            if cmd_txt in module:
                embed = discord.Embed(type='rich', color=0xFF9900, title='⚠ Error')
                embed.add_field(name='Unable to set command', value=f'Cannot set a default command')
                await msg.channel.send(None, embed=embed)
                return

        # Add to db
        table = self.db.table('custom_cmds')

        entry = table.get(doc_id=msg.guild.id)
        if isinstance(entry, type(None)):
            entry = Document({ cmd_txt : cmd_msg }, doc_id=msg.guild.id)

        entry[cmd_txt] = cmd_msg
        table.upsert(entry)

        # Register command
        self._cmds[f'{msg.guild.id}_{cmd_txt}'] = {
            'func'     : lambda bot, msg: CmdsModeration.__custom_command(bot, msg, cmd_server_id=entry.doc_id, cmd_txt=cmd_msg),
            'perm'     : DiscordCmdBase.ANYONE,
            'anywhere' : True,
            'example'  : None,
            'help'     : None,
        }

        embed = discord.Embed(title=f'Set {DiscordBot.cmd_prefix}{cmd_txt} command', color=0x1ABC9C)
        await msg.channel.send(None, embed=embed)


    @DiscordCmdBase.DiscordCmd(
        perm     = DiscordCmdBase.MODERATOR,
        example  = f'{DiscordBot.cmd_prefix}bot.cmd.rmv [cmd]',
        help     =
            'Removes a custom command.'
    )
    async def bot_cmd_rmv(self: DiscordBot, msg: discord.Message, *args: "list[str]"):
        """
        Data fmt:
            "custom_cmds": {
                (server.id: str): {
                    (cmd: str) : (msg: str),
                    (cmd: str) : (msg: str),
                    ...
                },
                ...
            }
        """
        if not msg.author.guild_permissions.manage_channels:
            embed = discord.Embed(type='rich', color=0xFF9900, title='⚠ Error')
            embed.add_field(name='Insufficient permissions', value=f'You need the manage channel permission to use this command')
            await msg.channel.send(None, embed=embed)

        if len(args) != 1:
            await self.run_help_cmd(msg, 'bot.cmd.rmv')
            return

        cmd_txt = args[0]

        for module in self._modules.values():
            if cmd_txt in module:
                embed = discord.Embed(type='rich', color=0xFF9900, title='⚠ Error')
                embed.add_field(name='Unable to remove command', value=f'Cannot remove a default command')
                await msg.channel.send(None, embed=embed)
                return

        # Remove from db
        table = self.db.table('custom_cmds')

        entry = table.get(doc_id=msg.guild.id)
        if isinstance(entry, type(None)):
            return

        if cmd_txt in entry:
            del entry[cmd_txt]

        table.update(entry)

        # Unregister command
        if f'{msg.guild.id}_{cmd_txt}' in self._cmds:
            del self._cmds[f'{msg.guild.id}_{cmd_txt}']

        embed = discord.Embed(title=f'Removed {DiscordBot.cmd_prefix}{cmd_txt} command', color=0x1ABC9C)
        await msg.channel.send(None, embed=embed)


    @DiscordCmdBase.DiscordEvent()
    async def register_custom_commands(self: DiscordBot):
        logger = logging.getLogger('reg_cmds')
        logger.info(f'Registering custom cmds...')

        table = self.db.table('custom_cmds')
        for entry in table.all():
            for cmd_txt, cmd_msg in entry.items():
                logger.info(f'    {cmd_txt}')
                self._cmds[f'{entry.doc_id}_{cmd_txt}'] = {
                    'func'     : lambda bot, msg, cmd_server_id=entry.doc_id, cmd_text=cmd_msg: CmdsModeration.__custom_command(bot, msg, cmd_server_id=cmd_server_id, cmd_txt=cmd_text),
                    'perm'     : DiscordCmdBase.ANYONE,
                    'anywhere' : True,
                    'example'  : None,
                    'help'     : None,
                }
