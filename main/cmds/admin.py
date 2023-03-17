import discord
import config
import requests

from main import DiscordCmdBase


class CmdsAdmin:

    @DiscordCmdBase.DiscordCmd(
        example = f'{config.cmd_prefix}kill',
        help    = 
            'Forcefully kill the bot.'
    )
    async def kill(self : discord.Client, msg : discord.Message):
        if msg.author.id != config.admin_user_id: 
            return

        status = discord.Embed(title=':skull_crossbones: Sigma Shutting Down.', color=0x808080)
        
        try: await msg.channel.send(None, embed=status)
        except: pass
    
        # Shutdown the discord client
        await self.close()

        # Shutdown the Feed server as well
        requests.put('http://127.0.0.1:5000/internal', json={
            'shutdown' : True
        })


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        example = f'{config.cmd_prefix}evaluate print("hello world")',
        help    = 
            'Executes raw python code. This should be used with caution.'
    )
    async def evaluate(self : discord.Client, msg : discord.Message):
        if msg.author.id != config.admin_user_id: 
            return
            
        # TODO
        pass
