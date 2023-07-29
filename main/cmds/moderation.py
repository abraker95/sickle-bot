import discord
import warnings

from tinydb.table import Document

from main import DiscordCmdBase, DiscordBot


class CmdsModeration:

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

        table = self.get_db_table('bot_en')
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

        table = self.get_db_table('bot_ch')
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
        table = self.get_db_table('bot_ch')
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

