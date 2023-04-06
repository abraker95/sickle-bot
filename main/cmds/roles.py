import discord
import config
import requests

from main import DiscordCmdBase



class CmdsRoles:

    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        example = f'{config.cmd_prefix}autorole Wizard',
        help    = 
            'Sets the role that should be given to the users that join '
            'the server. To disable the autorole input disable as the '
            'role name. Requires the user who calls the command to have '
            'the Administrator permision.'
    )
    async def autorole(self : discord.Client, msg : discord.Message, *args):
        pass


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        example = f'{config.cmd_prefix}createrole Cheese',
        help    = 
            'Creates a new role on the server. Requires the user who calls '
            'the command to have the Manage Roles permision.'
    )
    async def createrole(self : discord.Client, msg : discord.Message, *args):
        pass


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        example = f'{config.cmd_prefix}destroyrole Blergh',
        help    = 
            'Destroy an existing role on the server. Requires the user who '
            'calls the command to have the Manage Roles permision'
    )
    async def destroyrole(self : discord.Client, msg : discord.Message, *args):
        pass


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        example = f'{config.cmd_prefix}togglerole Wizard',
        help    = 
            'Assigns you or removes you from one of the self assignable roles. '
            'Self assignable roles are added via the addselfrole command. A '
            'list of self assignable roles can be seen with the listselfroles '
            'command.'
    )
    async def togglerole(self : discord.Client, msg : discord.Message, *args):
        pass


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        example = f'{config.cmd_prefix}addselfrole Cheese',
        help    = 
            'Makes a role self assignable. Requires the user who calls the command '
            'to have the Manage Roles permision.'
    )
    async def addselfrole(self : discord.Client, msg : discord.Message, *args):
        pass


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        example = f'{config.cmd_prefix}delselfrole Cheese',
        help    = 
            'Makes a role no longer self assignable. Requires the user who calls the '
            'command to have the Manage Roles permision.'
    )
    async def delselfrole(self : discord.Client, msg : discord.Message, *args):
        pass


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        example = f'{config.cmd_prefix}listselfroles',
        help    = 
            'Assigns you or removes you from one of the self assignable roles. Self '
            'assignable roles are added via the addrole command. A list of self '
            'assignable roles can be seen with the listselfroles command.'
    )
    async def listselfroles(self : discord.Client, msg : discord.Message, *args):
        pass

    
    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        example = f'{config.cmd_prefix}roles',
        help    = 
            'Lists all the roles on the server and the total number of roles.'
    )   
    async def roles(self : discord.Client, msg : discord.Message, *args):
        pass
