import discord
import config
import requests

import tinydb
from tinydb.table import Document

from main import DiscordCmdBase, DiscordBot


class CmdsModeration:

    @DiscordCmdBase.DiscordCmd(
        perm    = DiscordCmdBase.MODERATOR,
        example = f'{config.cmd_prefix}bot.en true',
        help    =
            'Enable/Disable the bot in the channel.'
    )
    async def bot_en(self: DiscordBot, msg: discord.Message, *args: str):
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

