import discord
import config
import requests
import warnings

from main import DiscordCmdBase, DiscordBot



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
    async def autorole(self: DiscordBot, msg: discord.Message, *args: str):
        if len(args) != 1:
            await self.run_help_cmd(msg, 'autorole')
            return

        # TODO


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        example = f'{config.cmd_prefix}createrole Cheese',
        help    = 
            'Creates a new role on the server. Requires the user who calls '
            'the command to have the Manage Roles permision.'
    )
    async def createrole(self: DiscordBot, msg: discord.Message, *args: str):
        if len(args) != 1:
            await self.run_help_cmd(msg, 'createrole')
            return

        if not msg.author.guild_permissions.manage_roles:
            embed = discord.Embed(type='rich', color=0xDB0000, title='⛔ Insufficient Permissions. Requires Manage Roles permision.')
            await msg.channel.send(None, embed=embed)
            return

        role_name = args[0].lower()
        role_names = map(lambda role: role.name.lower(), msg.guild.roles)

        if role_name in role_names:
            embed = discord.Embed(type='rich', color=0xFF9900, title='⚠ Error')
            embed.add_field(name='Role Exists', value=f'A role with the name **{role_name}** already exists.')
            await msg.channel.send(None, embed=embed)
            return

        await msg.guild.create_role(name=role_name)
        embed = discord.Embed(type='rich', color=0x33CC33, title=f'✅ Role {role_name} created.')
        await msg.channel.send(None, embed=embed)


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        example = f'{config.cmd_prefix}destroyrole Blergh',
        help    = 
            'Destroy an existing role on the server. Requires the user who '
            'calls the command to have the Manage Roles permision'
    )
    async def destroyrole(self: DiscordBot, msg: discord.Message, *args: str):
        if len(args) != 1:
            await self.run_help_cmd(msg, 'destroyrole')
            return

        if not msg.author.guild_permissions.manage_roles:
            embed = discord.Embed(type='rich', color=0xDB0000, title='⛔ Insufficient Permissions. Requires Manage Roles permision.')
            await msg.channel.send(None, embed=embed)
            return

        role_name = args[0].lower()
        roles = list([ role for role in msg.guild.roles if role.name.lower() == role_name ])

        if len(roles) == 0:
            embed = discord.Embed(type='rich', color=0xFF9900, title='⚠ Error')
            embed.add_field(name='Role Not Found', value=f'Unable to find role with the name **{role_name}** on this server.')
            await msg.channel.send(None, embed=embed)
            return

        for role in roles:
            await role.delete()

            embed = discord.Embed(type='rich', color=0x66cc66, title=f'✅ Role {role} (id: {role.id}) destroyed.')
            await msg.channel.send(None, embed=embed)


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        example = f'{config.cmd_prefix}togglerole Wizard',
        help    = 
            'Assigns you or removes you from one of the self assignable roles. '
            'Self assignable roles are added via the addselfrole command. A '
            'list of self assignable roles can be seen with the listselfroles '
            'command.'
    )
    async def togglerole(self: DiscordBot, msg: discord.Message, *args: str):
        if len(args) != 1:
            await self.run_help_cmd(msg, 'togglerole')
            return

        role_name = args[0].lower()
        roles = list([ role for role in msg.guild.roles if role.name.lower() == role_name ])

        if len(roles) == 0:
            embed = discord.Embed(type='rich', color=0xFF9900, title='⚠ Error')
            embed.add_field(name='Role Not Found', value=f'Unable to find server role with the name **{role_name}** on this server.')
            await msg.channel.send(None, embed=embed)
            return

        if len(roles) > 1:
            # NOTE: Shouldn't happen
            warnings.warn('Found more than one server role')

        server_role = roles[0]
        roles = list([ role for role in msg.author.roles if role.name.lower() == role_name ])

        if len(roles) == 0:
            # At this point user does not have role and we want to add it
            if server_role.permissions <= msg.author.guild_permissions:
                await msg.author.add_roles(server_role)

                embed = discord.Embed(title=f'✅ {role_name} has been added to you.', color=0x66cc66)
                await msg.channel.send(None, embed=embed)
                return

            embed = discord.Embed(type='rich', color=0xDB0000, title='⛔ Insufficient Permissions. You do not have sufficient permissions for this role.')
            await msg.channel.send(None, embed=embed)
            return

        # At this point the user has the role and we want to remove it

        if len(roles) > 1:
            # NOTE: Shouldn't happen
            warnings.warn('Found more than one user role')

        await msg.author.remove_roles(server_role)
        
        embed = discord.Embed(title=f'⚠ {role_name} has been removed from you.', color=0xFF9900)        
        await msg.channel.send(None, embed=embed)
        return


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        example = f'{config.cmd_prefix}addselfrole Cheese',
        help    = 
            'Makes a role self assignable. Requires the user who calls the command '
            'to have the Manage Roles permision.'
    )
    async def addselfrole(self: DiscordBot, msg: discord.Message, *args: str):
        if len(args) != 1:
            await self.run_help_cmd(msg, 'addselfrole')
            return

        if not msg.author.guild_permissions.manage_roles:
            embed = discord.Embed(type='rich', color=0xDB0000, title='⛔ Insufficient Permissions. Requires Manage Roles permision.')
            await msg.channel.send(None, embed=embed)
            return

        # TODO


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        example = f'{config.cmd_prefix}delselfrole Cheese',
        help    = 
            'Makes a role no longer self assignable. Requires the user who calls the '
            'command to have the Manage Roles permision.'
    )
    async def delselfrole(self: DiscordBot, msg: discord.Message, *args: str):
        if len(args) != 1:
            await self.run_help_cmd(msg, 'delselfrole')
            return

        if not msg.author.guild_permissions.manage_roles:
            embed = discord.Embed(type='rich', color=0xDB0000, title='⛔ Insufficient Permissions. Requires Manage Roles permision.')
            await msg.channel.send(None, embed=embed)
            return

        # TODO


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        example = f'{config.cmd_prefix}listselfroles',
        help    = 
            'Assigns you or removes you from one of the self assignable roles. Self '
            'assignable roles are added via the addrole command. A list of self '
            'assignable roles can be seen with the listselfroles command.'
    )
    async def listselfroles(self: discord.Client, msg: discord.Message, *args: str):
        # TODO

        pass

    
    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        example = f'{config.cmd_prefix}roles',
        help    = 
            'Lists all the roles on the server and the total number of roles.'
    )   
    async def roles(self: DiscordBot, msg: discord.Message, *args: str):
        roles_names = list([ role.name for role in msg.guild.roles ])

        role_list = '\n'.join(roles_names)
        if len(role_list) > 1800:
            role_list = role_list[:1800] + '...'

        embed = discord.Embed(color=0x1ABC9C)
        embed.add_field(name=f'There Are {len(roles_names)} roles on {msg.guild.name}', value=f'```\n{role_list}\n```')
        await msg.channel.send(None, embed=embed)


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        example = f'{config.cmd_prefix}selfroles @user',
        help    = 
            'Lists all the roles the user can assign to themselves, or another user can assign to themselves.'
    )   
    async def selfroles(self: discord.Client, msg: discord.Message, *args: str):
        user = None

        if len(args) == 0:
            user = msg.author

        if len(args) == 1:
            if len(msg.mentions) == 0:
                await self._cmds['help']['func'](self, msg, 'selfroles')
                return

            user = msg.mentions[0]

        if len(args) > 1:
            await self._cmds['help']['func'](self, msg, 'xkcd')
            return
                
        user = msg.mentions[0] if msg.mentions else msg.author
        roles = list([ role for role in msg.guild.roles if role.permissions <= user.guild_permissions ])
        
        role_list = '\n'.join([ f'{role.name}' for role in roles ])
        if len(role_list) > 1800:
            role_list = role_list[:1800] + '...'

        embed = discord.Embed(color=0x1ABC9C)
        embed.add_field(name=f'{user.name} can assign the following roles to themselves', value=f'```\n{role_list}\n```')
        await msg.channel.send(None, embed=embed)
