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
    async def help(self : discord.Client, msg : discord.Message, cmd=None):
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
            reply.add_field(name='Command Usage Example and Information', value=self._cmds[cmd]['help'])
            
        try: await msg.channel.send(None, embed=reply)
        except:
            self.get_logger(self).warning(f'"{__name__}" cmd fail send to - {msg.guild.name} : {msg.channel.name}')


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        example = f'{config.cmd_prefix}commands Games',
        help    = 
            'Shows the commands in a specific module group.'
    )
    async def commands(self : discord.Client, msg : discord.Message, module: str = None):
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
    async def ping(self : discord.Client, msg : discord.Message):
        reply = discord.Embed(title='Pong!', color=0x0099FF)

        try: await msg.channel.send(None, embed=reply)
        except:
            self.get_logger(self).warning(f'"{__name__}" cmd fail send to - {msg.guild.name} : {msg.channel.name}')
