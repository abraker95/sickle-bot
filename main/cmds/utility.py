import os
import time
import datetime
from typing import Optional, Union, Tuple

from PIL import Image, ImageColor

import discord
import config
import requests

from main import DiscordCmdBase



class CmdsUtility:

    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        example = f'{config.cmd_prefix}help [command]',
        help    = 
            'Returns the list of command modules or gives you the '
            'description and usage for a selected command.'
    )
    async def help(self: discord.Client, msg: discord.Message, cmd: Optional[str] = None):
        if isinstance(cmd, type(None)):
            reply = discord.Embed(type='rich', title='❔Help❔', color=0x2cefe5)
        
            reply.add_field(name=' Sickle\'s Module List', value='```yaml\n' + '\n'.join(self._modules) + '\n```', inline=True)
            reply.add_field(name='Please submit bugs, issues, or suggestions here.', value='[**LINK**](https://github.com/abraker95/sickle-bot/issues)', inline=True)
            reply.add_field(name='Add me to your server!', value='[**LINK**](https://discordapp.com/oauth2/authorize?&client_id=290355925317976074&scope=bot&permissions=0)', inline=True)
        
            reply.add_field(name='Sickle in its natural habitat', value='⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀ ⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿\n'+'⠀⠀⠀⠀⣿⣿⣿⣿⠀⠀⠀⠀⠀⠀⣄ ⣠⠀⠀⠀⠀⠀⣿⣿⣿⣿\n'+'⠀⠀⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀⠀⣿⣿⣿⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿\n'+'⣿⠋⠀⠀⠀⠀⠀⠀⠀⠙⣿⣿⣿⣿⣿⣿⣿⠋⠈⠀⠀⠀⠀⠀⠀⠀⠙⣿\n'+'⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈\n'+'⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠀⠀⠀⠈', inline=True)
            reply.set_footer(text=f'Use {config.cmd_prefix}commands <module> to get a list of commands available in that module.\n Use {config.cmd_prefix}help <command> to get a description about the command usage.')
            reply.set_image(url='https://i.imgur.com/UOzJ31H.png')
        
            try: await msg.channel.send(None, embed=reply)
            except:
                self.get_logger(self).warning(f'"{__name__}" cmd fail send to - {msg.guild.name} : {msg.channel.name}')

            return
        
        if cmd not in self._cmds:
            reply = discord.Embed(type='rich', color=0x696969, title='🔍 No such command was found...')
        else:
            reply = discord.Embed(title=f':book: HELP {cmd}', color=0x1B6F5F)
            reply.add_field(
                name = 'Command Usage Example and Information', 
                value = 
                    f"Example: `{self._cmds[cmd]['example']}`\n"
                    "```\n"
                    f"{self._cmds[cmd]['help']}\n"
                    "```"
            )
            
        try: await msg.channel.send(None, embed = reply)
        except:
            self.get_logger(self).warning(f'"{__name__}" cmd fail send to - {msg.guild.name} : {msg.channel.name}')


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        example = f'{config.cmd_prefix}commands Games',
        help    = 
            'Shows the commands in a specific module group.'
    )
    async def commands(self: discord.Client, msg: discord.Message, module: str = None):
        if isinstance(module, type(None)):
            embed = discord.Embed(color=0x696969, title='🔍 Please Enter a Module Name.')
            embed.set_footer(text=f'The module groups can be seen with the {config.cmd_prefix}help command.')
            await msg.channel.send(None, embed=embed)
            return

        if module not in self._modules:
            embed = discord.Embed(color=0x696969, title='🔍 Module Group Not Found!')
            await msg.channel.send(None, embed=embed)
            return
        
        reply = discord.Embed(color=0x1abc9c)
        reply.add_field(name=f'Sickle\'s commands in {module}', value='```yaml\n' + ', '.join(self._modules[module]) + '\n```')
        await msg.channel.send(None, embed=reply)


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        example = f'{config.cmd_prefix}ping',
        help    = 
            'just prints "pong!". Useful to know if the bot is up'
    )
    async def ping(self: discord.Client, msg: discord.Message):
        reply = discord.Embed(title='Pong!', color=0x0099FF)

        try: await msg.channel.send(None, embed=reply)
        except:
            self.get_logger(self).warning(f'"{__name__}" cmd fail send to - {msg.guild.name} : {msg.channel.name}')


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        example = f'{config.cmd_prefix}uid @person',
        help    = 
            'Shows the User ID of the mentioned user. If no user is mentioned, it will show your ID instead.'
    )
    async def uid(self: discord.Client, msg: discord.Message, *args):
        user = msg.mentions[0] if msg.mentions else msg.author

        embed = discord.Embed(color=0x0099FF)
        embed.add_field(name='ℹ ' + user.name, value=f'`{user.id}`')
        await msg.channel.send(None, embed=embed)


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        example = f'{config.cmd_prefix}color #1ABC9C',
        help    = 
            'Generates a color from the given HEX code or provided RGB numbers.'
    )
    async def color(self: discord.Client, msg: discord.Message, *args):
        if len(args) == 0:
            await self._cmds['help']['func'](self, msg, 'color')
            return

        rgb = None

        if len(args) == 1:
            # Interpret as hex
            rgb = ImageColor.getcolor(args[0], 'RGB')

        if len(args) == 3:
            # Interpret as (r, g, b)
            for arg in args:
                if not 0 <= int(arg) <= 255:
                    await msg.channel.send(None, 'Error processing inputted variables.\n 0 <= R G B <= 255.')
                    return
                    
            rgb = (int(args[0]), int(args[1]), int(args[2]))

        if isinstance(rgb, type(None)):
            await msg.channel.send('Error processing inputted variables.')
            return
        
        img = Image.new('RGB', (50, 50), rgb)
        img.save(f'cache/{msg.author.id}.png')
        
        await msg.channel.send(file=discord.File(f'cache/{msg.author.id}.png'))
        
        os.remove(f'cache/{msg.author.id}.png')


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        example = f'{config.cmd_prefix}avatar @person',
        help    = 
            'Shows the avatar of the user. (in the form of a direct link)'
    )
    async def avatar(self: discord.Client, msg: discord.Message, *args):
        target = msg.mentions[0] if msg.mentions else msg.author
    
        embed = discord.Embed(color=target.color)
        embed.set_image(url=target.avatar.url)
        await msg.channel.send(None, embed=embed)


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        example = f'{config.cmd_prefix}timestamp 2023-02-12 12:23 UTC+4',
        help    = 
            'Generates a discord timestamp from the date given'
    )
    async def timestamp(self: discord.Client, msg: discord.Message, *args):
        if isinstance(args, type(None)):
            await self._cmds['help']['func'](self, msg, 'timestamp')
            return

        if len(args) != 3:
            await self._cmds['help']['func'](self, msg, 'timestamp')
            return

        date_str = ' '.join(args)
        
        idx = date_str.find('UTC')
        if idx == -1:
            date_str += 'UTC+0000'
        else:
            # Skip the "UTC+" / "UTC-" part
            idx += 4

            # Make sure timezone info is in UTC+#### (4 digit formatting)
            if len(date_str[idx:]) == 1:
                date_str = date_str[:idx] + f'0{date_str[idx:]}00'
            if len(date_str[idx:]) == 2:
                date_str += '00'

        timestamp = datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M %Z%z').timestamp()
        await msg.channel.send(f'<t:{int(timestamp)}>')


