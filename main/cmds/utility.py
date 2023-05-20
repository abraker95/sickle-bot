import os
import random
import datetime
import arrow
import asyncio
import logging
import warnings

from typing import Optional

from PIL import Image, ImageColor

import discord
import config

import tinydb
from tinydb.table import Document

from main import DiscordCmdBase, DiscordBot



class CmdsUtility:

    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        perm    =  DiscordCmdBase.ANYONE,
        example = f'{config.cmd_prefix}help [command]',
        help    =
            'Returns the list of command modules or gives you the '
            'description and usage for a selected command.'
    )
    async def help(self: DiscordBot, msg: discord.Message, cmd: Optional[str] = None, *args: str):
        if isinstance(cmd, type(None)):
            modules_text = '\n'.join(self._modules)

            embed = discord.Embed(type='rich', title='❔Help❔', color=0x2cefe5)

            embed.add_field(
                name  = 'Sickle\'s Module List',
                value = (
                    '```yaml\n'
                    f'{modules_text}' + '\n'
                    '```'
                ),
                inline = True
            )
            embed.add_field(name='Please submit bugs, issues, or suggestions here.', value='[**LINK**](https://github.com/abraker95/sickle-bot/issues)', inline=True)
            embed.add_field(name='Add me to your server!', value='[**LINK**](https://discordapp.com/oauth2/authorize?&client_id=290355925317976074&scope=bot&permissions=0)', inline=True)
            embed.add_field(
                name  = 'Sickle in its natural habitat',
                value = (
                    '⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀ ⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿\n'
                    '⠀⠀⠀⠀⣿⣿⣿⣿⠀⠀⠀⠀⠀⠀⣄ ⣠⠀⠀⠀⠀⠀⣿⣿⣿⣿\n'
                    '⠀⠀⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀⠀⣿⣿⣿⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿\n'
                    '⣿⠋⠀⠀⠀⠀⠀⠀⠀⠙⣿⣿⣿⣿⣿⣿⣿⠋⠈⠀⠀⠀⠀⠀⠀⠀⠙⣿\n'
                    '⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈\n'
                    '⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠀⠀⠀⠈'
                ),
                inline = True
            )

            embed.set_footer(text=
                f'Use {config.cmd_prefix}commands <module> for list of commands available in that module.\n'
                f'Use {config.cmd_prefix}help <command> for description about the command usage.\n'
                '\n'
                f'{self.get_version()}'
            )
            embed.set_image(url='https://i.imgur.com/UOzJ31H.png')

            await msg.channel.send(None, embed=embed)
            return

        if cmd not in self._cmds:
            embed = discord.Embed(type='rich', color=0x696969, title='🔍 No such command was found...')
            await msg.channel.send(None, embed=embed)
            return

        embed = discord.Embed(title=f':book: HELP {cmd}', color=0x1B6F5F)
        embed.add_field(
            name = 'Command Usage Example and Information',
            value =
                f'Example: `{self._cmds[cmd]["example"]}`\n'
                '```\n'
                f'{self._cmds[cmd]["help"]}\n'
                '```'
        )

        await msg.channel.send(None, embed=embed)


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        perm    = DiscordCmdBase.ANYONE,
        example = f'{config.cmd_prefix}commands Games',
        help    =
            'Shows the commands in a specific module group.'
    )
    async def commands(self: DiscordBot, msg: discord.Message, module: str = None, *args: str):
        if isinstance(module, type(None)):
            embed = discord.Embed(color=0x696969, title='🔍 Please Enter a Module Name.')
            embed.set_footer(text=f'The module groups can be seen with the {config.cmd_prefix}help command.')
            await msg.channel.send(None, embed=embed)
            return

        if module not in self._modules:
            embed = discord.Embed(color=0x696969, title='🔍 Module Group Not Found!')
            await msg.channel.send(None, embed=embed)
            return

        embed = discord.Embed(color=0x1abc9c)
        embed.add_field(name=f'Sickle\'s commands in {module}', value='```yaml\n' + ', '.join(self._modules[module]) + '\n```')
        await msg.channel.send(None, embed=embed)


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        perm    = DiscordCmdBase.ANYONE,
        example = f'{config.cmd_prefix}devs A command that gives sickle a cookie :cookie:',
        help    =
            'Message the devs a suggestion or issues'
    )
    async def devs(self: DiscordBot, msg: discord.Message, *args: str):
        await self.msg_dev(msg.guild, msg.author, ' '.join(args))

        embed = discord.Embed(color=0x0099FF, title='Your message has reached the devs!')
        await msg.channel.send(None, embed=embed)


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        perm    = DiscordCmdBase.ANYONE,
        example = f'{config.cmd_prefix}ping',
        help    =
            'Just prints "pong!". Useful to know if the bot is up'
    )
    async def ping(self: DiscordBot, msg: discord.Message, *args: str):
        ms = arrow.utcnow().timestamp() - msg.created_at.timestamp()
        embed = discord.Embed(title=f'Pong! ({ms:.2f} s)', color=0x0099FF)
        await msg.channel.send(None, embed=embed)


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        perm    = DiscordCmdBase.ANYONE,
        example = f'{config.cmd_prefix}cmd.stats',
        help    =
            'Prints command usage stats for this server'
    )
    async def cmd_stats(self: DiscordBot, msg: discord.Message, *args: str):
        if msg.author.id != config.admin_user_id:
            status = discord.Embed(title='You must be the bot admin to use this command', color=0x800000)
            await msg.channel.send(None, embed=status)
            return

        cmd_counts = {}
        for cmd in self._cmds:
            if self._cmds[cmd]['perm'] == DiscordCmdBase.ADMINISTRATOR:
                # Don't give stats for admin commands
                continue

            cmd_counts[cmd] = self.db_get_cmd_server_count(msg.guild.id, cmd)

        cmd_names_txt = '\n'.join(map(str, cmd_counts.keys()))
        cmd_stats_txt = '\n'.join(map(str, cmd_counts.values()))

        reply = discord.Embed(color=0x1abc9c)
        reply.set_author(name='Command Stats')
        reply.add_field(name='', value=f'```{cmd_names_txt}```', inline=True)
        reply.add_field(name='', value=f'```{cmd_stats_txt}```', inline=True)
        reply.set_footer(text=f'In {msg.guild.name}')

        await msg.channel.send(None, embed=reply)


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        perm    = DiscordCmdBase.ANYONE,
        example = f'{config.cmd_prefix}color #1ABC9C',
        help    =
            'Generates a color from the given HEX code or provided RGB numbers.'
    )
    async def color(self: DiscordBot, msg: discord.Message, *args: str):
        if len(args) == 0:
            await self.run_help_cmd(msg, 'color')
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
        perm    = DiscordCmdBase.ANYONE,
        example = f'{config.cmd_prefix}avatar @person',
        help    =
            'Shows the avatar of the user. (in the form of a direct link)'
    )
    async def avatar(self: DiscordBot, msg: discord.Message, *args: str):
        target = msg.mentions[0] if msg.mentions else msg.author

        embed = discord.Embed(color=target.color)
        embed.set_image(url=target.avatar.url)
        await msg.channel.send(None, embed=embed)


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        perm    = DiscordCmdBase.ANYONE,
        example = f'{config.cmd_prefix}uid @person',
        help    =
            'Shows the User ID of the mentioned user. If no user is mentioned, it will show your ID instead.'
    )
    async def uid(self: DiscordBot, msg: discord.Message, *args: str):
        user = msg.mentions[0] if msg.mentions else msg.author

        embed = discord.Embed(color=user.color)
        embed.add_field(name=user.name, value=f'`{user.id}`')
        await msg.channel.send(None, embed=embed)


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        perm    = DiscordCmdBase.ANYONE,
        example = f'{config.cmd_prefix}timestamp 2023-02-12 12:23 UTC+4',
        help    =
            'Generates a discord timestamp from the date given'
    )
    async def timestamp(self: DiscordBot, msg: discord.Message, *args: str):
        if isinstance(args, type(None)):
            await self.run_help_cmd(msg, 'timestamp')
            return

        if len(args) != 3:
            await self.run_help_cmd(msg, 'timestamp')
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


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        perm    = DiscordCmdBase.ANYONE,
        example = f'{config.cmd_prefix}echo Hello world!',
        help    =
            'Repeats the given text.'
    )
    async def echo(self: DiscordBot, msg: discord.Message, *args: str):
        await msg.channel.send(msg.content)


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        perm    = DiscordCmdBase.ANYONE,
        example = f'{config.cmd_prefix}poll Want to eat?; Yes; No; Hand me the cheese',
        help    =
            'Creates a poll with the items from the inputted list. '
            'Separate list items with a semicolon and a space.'
    )
    async def poll(self: DiscordBot, msg: discord.Message, *args: str):
        if isinstance(args, type(None)):
            reply = discord.Embed(type='rich', color=0xDB0000, title='❗ Missing Arguments.')
            await msg.channel.send(None, embed=reply)
            return

        all_qry = ' '.join(args)
        if all_qry.endswith(';'):
            all_qry = all_qry[:-1]

        poll_name = all_qry.split('; ')[0]
        choice_qry = '; '.join(all_qry.split('; ')[1:])

        if choice_qry.endswith(';'):
            choice_qry = choice_qry[:-1]

        poll_choices = choice_qry.split('; ')

        if len(poll_choices) < 2:
            reply = discord.Embed(type='rich', color=0xDB0000, title='❗ Not enough arguments present.')
            await msg.channel.send(None, embed=reply)
            return

        if len(poll_choices) > 9:
            reply = discord.Embed(type='rich', color=0xDB0000, title='❗ Maximum is 9 choices.')
            await msg.channel.send(None, embed=reply)
            return

        reaction_list = [ '🍏', '🍍', '🍐', '🌶', '🍆', '🍋', '🍌', '🍅', '🍓', '🍇' ]
        random.shuffle(reaction_list, random.random)
        choice_text = ''

        for i, option in enumerate(poll_choices):
            choice_text += f'\n{reaction_list[i]} - **{option}**'

        reply = discord.Embed(color=0x1ABC9C)
        reply.add_field(name=poll_name, value=choice_text)
        poll_message = await msg.channel.send(None, embed=reply)

        for i, option in enumerate(poll_choices):
            await poll_message.add_reaction(reaction_list[i])


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        perm    = DiscordCmdBase.ANYONE,
        example = f'{config.cmd_prefix}remind 1:03:15 LEEEEROOOOY JEEEEEENKIIIIINS!',
        help    =
            'Sets a timer in seconds and displays the message input after it\'s done.'
    )
    async def remind(self: DiscordBot, msg: discord.Message, *args: str):
        """
        Data fmt:
            "reminders": {
                (id: str): {
                    'user_id'     : (msg.author.id: int),
                    'channel_id'  : (msg.channel.id: int),
                    'server_id'   : (msg.guild.id: int),
                    'created_at'  : (now.timestamp: float),
                    'due_at'      : (due.timestamp: float),
                    'text'        : (text: str)
                },
                ...
            }
        """
        if isinstance(args, type(None)):
            embed = discord.Embed(color=0xDB0000, title='❗ No arguments inputted.')
            await msg.channel.send(embed=embed)
            return

        delta_seconds = None

        try: delta_seconds = float(args[0])
        except ValueError:
            pass

        if isinstance(delta_seconds, type(None)):
            try: delta_seconds = arrow.get(args[0], [ 'HH:mm:ss', 'HH:mm', 'H:mm:ss', 'H:mm' ]).timestamp() - arrow.get('00:00:00', 'HH:mm:ss').timestamp()
            except arrow.ParserError:
                embed = discord.Embed(color=0xDB0000, title='❗ Invalid time format.')
                await msg.channel.send(embed=embed)
                return

        if len(args) > 1:
            text = ' '.join(args[1:])
        else:
            text = 'No reminder message set.'

        due_timestamp = arrow.utcnow().timestamp() + delta_seconds

        if delta_seconds < 60:
            time_diff = f'In {delta_seconds} seconds'
        else:
            try: time_diff = arrow.get(due_timestamp).humanize(arrow.utcnow())
            except ValueError:
                embed = discord.Embed(color=0xDB0000, title='❗ Value too large.')
                await msg.channel.send(embed=embed)
                return

        data = {
            'user_id'     : msg.author.id,
            'channel_id'  : msg.channel.id,
            'server_id'   : msg.guild.id,
            'created_at'  : arrow.utcnow().timestamp(),
            'due_at'      : due_timestamp,
            'text'        : text
        }

        table = self.get_db_table('reminders')
        table.insert(Document(data, doc_id=msg.id))

        embed = discord.Embed(color=0x66CC66, timestamp=arrow.get(due_timestamp).datetime)
        embed.set_author(name='New Reminder Set', icon_url=msg.author.avatar.url)
        embed.add_field(name='🕑 Until Reminder', value=time_diff.title(), inline=False)
        embed.add_field(name='🗒 Reminder Message', value=text, inline=False)

        await msg.channel.send(embed=embed)


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        perm    = DiscordCmdBase.ANYONE,
        example = f'{config.cmd_prefix}reminders 3',
        help    =
            'Shows you a list of up to five pending reminders that you made. '
            'Input a number after the command to see more details about that reminder.'
    )
    async def reminders(self: DiscordBot, msg: discord.Message, *args: str):
        table = self.get_db_table('reminders')
        entries = table.search(tinydb.Query().fragment({ 'server_id' : msg.guild.id, 'user_id' : msg.author.id }))

        num_reminders = len(entries)
        if num_reminders == 0:
            embed = discord.Embed(color=0x696969, title='🔍 You have not made any reminders.')
            await msg.channel.send(embed=embed)
            return

        if len(args) == 0:
            reminders_str = ''

            for rem in entries[:5]:
                time_str = arrow.get(rem['due_at']).humanize(arrow.utcnow())
                reminders_str += (
                    f'\n**{rem["text"]}**'
                    f'\n  - {time_str}'
                )

            embed = discord.Embed(color=0x0099FF)
            embed.add_field(name=f'ℹ Reminder Data', value=f'You have {num_reminders} pending reminders.', inline=False)
            embed.add_field(name='Upcoming Reminders', value=reminders_str, inline=False)
            embed.set_footer(text=f'To see their details type {config.cmd_prefix}reminders [0-{num_reminders - 1}]')
            await msg.channel.send(embed=embed)
            return

        try: i = int(args[0])
        except ValueError:
            embed = discord.Embed(color=0x993333, title=f':exclamation: Enter a number within the range 0 to {num_reminders - 1}, inclusive')
            await msg.channel.send(embed=embed)
            return

        try: choice = entries[i]
        except IndexError:
            embed = discord.Embed(color=0x993333, title=f':exclamation: Enter a number within the range 0 to {num_reminders - 1}, inclusive')
            await msg.channel.send(embed=embed)
            return

        creation_stamp = arrow.get(choice['created_at'])
        creation_human = creation_stamp.humanize(arrow.utcnow())
        creation_date = creation_stamp.format('YYYY-MM-DD HH:mm:ss')

        execution_stamp = arrow.get(choice['due_at'])
        execution_human = execution_stamp.humanize(arrow.utcnow())
        execution_date = execution_stamp.format('YYYY-MM-DD HH:mm:ss')

        embed = discord.Embed(color=0x0099FF)
        embed.set_author(name='🕙 Reminder Information', icon_url=msg.author.avatar.url)
        embed.add_field(name='Created', value=f'{creation_human.title()}\n{creation_date} UTC', inline=True)
        embed.add_field(name='Executes', value=f'{execution_human.title()}\n{execution_date} UTC', inline=True)
        embed.add_field(name='Message', value=f'{choice["text"]}', inline=False)
        embed.set_footer(text=f'ReminderID: {choice.doc_id}')
        await msg.channel.send(embed=embed)


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        perm    = DiscordCmdBase.ANYONE,
        example = f'{config.cmd_prefix}roll 701',
        help    =
            'Gives a random number from 0 to 100. You can specify the highest number '
            'the function calls by adding a number after the command. The Number '
            'TECHNICALLY does not have a limit but the bigger you use, the bigger '
            'the message, which just looks plain spammy.'
    )
    async def roll(self: DiscordBot, msg: discord.Message, *args: str):
        end_range = None

        if len(args) > 0:
            try: end_range = int(args[0])
            except ValueError:
                await self.run_help_cmd(msg, 'roll')
                return

        if isinstance(end_range, type(None)):
            end_range = 100

        num = random.randint(1, end_range)

        embed = discord.Embed(color=0x1abc9c)
        embed.add_field(name='🎲 You Rolled', value=f'```\n{num}\n```')
        await msg.channel.send(None, embed=embed)


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        perm    = DiscordCmdBase.ANYONE,
        example = f'{config.cmd_prefix}choose Pizza Burgers Both',
        help    =
            'The bot will select a thing from the inputed list. Separate list '
            'items with a space.'
    )
    async def choose(self: DiscordBot, msg: discord.Message, *args: str):
        if len(args) == 0:
            await self.run_help_cmd(msg, 'choose')
            return

        choice = random.choice(args)
        embed = discord.Embed(color=0x1ABC9C, title=':thinking: I choose... ' + choice)
        await msg.channel.send(None, embed=embed)


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        perm    = DiscordCmdBase.ANYONE,
        example = f'{config.cmd_prefix}serverinfo',
        help    =
            'Shows information about the server the command was used on.'
    )
    async def serverinfo(self: DiscordBot, msg: discord.Message, *args: str):
        bot_count = 0
        user_count = 0

        for user in msg.guild.members:
            if user.bot:
                bot_count += 1
            else:
                user_count += 1

        embed = discord.Embed(title=msg.guild.name + ' Information', color=0x1ABC9C)
        embed.add_field(name='Name',         value=f'```python\n{msg.guild.name}\n```')
        embed.add_field(name='Server ID',    value=f'```python\n{msg.guild.id}\n```')
        embed.add_field(name='Created',      value=f'```python\n{msg.guild.created_at}\n```')
        embed.add_field(name='Member Count', value=f'```python\n{user_count} (+{bot_count} bots)\n```')
        if msg.guild.owner:
            embed.add_field(name='Owner',        value=f'```python\n{msg.guild.owner.name}\n```')
            embed.add_field(name='Owner ID',     value=f'```python\n{msg.guild.owner.id}\n```')
        embed.add_field(name='Verif. Level', value=f'```python\n{msg.guild.verification_level.name}\n```')
        embed.add_field(name='MFA Level',    value=f'```python\n{msg.guild.mfa_level.name}\n```')

        if msg.guild.afk_channel:
            embed.add_field(name='AFK Channel', value=f'```python\n{msg.guild.afk_channel.name}\n```')
            embed.add_field(name='AFK Timeout', value=f'```python\n{msg.guild.afk_timeout}\n```')

        await msg.channel.send(None, embed=embed)


    @staticmethod
    @DiscordCmdBase.DiscordCmd(
        perm    = DiscordCmdBase.ANYONE,
        example = f'{config.cmd_prefix}userinfo @person',
        help    =
            'Shows information about the mentioned user. If no user is mentioned, '
            'it will show information about you, instead.'
    )
    async def userinfo(self: DiscordBot, msg: discord.Message, *args: str):
        user = msg.mentions[0] if len(args) > 0 else msg.author

        embed = discord.Embed(title=f'{user.name} Information', color=user.color)
        embed.add_field(name='Username', value=f'```python\n{user.name}#{user.discriminator}\n```')
        embed.add_field(name='User ID',  value=f'```python\n{user.id}\n```')
        if user.nick:
            embed.add_field(name='Nickname', value=f'```python\n{user.nick}\n```')
        embed.add_field(name='Joined', value=f'```python\n{user.created_at}\n```')
        embed.add_field(name='Status', value=f'```python\n{user.status.name}\n```')
        if user.roles:
            embed.add_field(name='Status', value=f'```python\n{user.top_role.name}\n```')
        embed.add_field(name='Color',  value=f'```python\n{user.color}\n```')
        embed.add_field(name='Is bot', value=f'```python\n{user.bot}\n```')

        await msg.channel.send(None, embed=embed)


    @DiscordCmdBase.DiscordEvent()
    async def reminder_task(self: DiscordBot):
        logger = logging.getLogger('reminder_task')

        while True:
            # Process reminders every second
            await asyncio.sleep(1)
            # logger.debug(f'tick @ {time.time()}')

            table = self.get_db_table('reminders')
            for guild in self.guilds:
                # Sleep to yield db search
                await asyncio.sleep(0.1)

                entries = table.search(tinydb.Query().fragment({ 'server_id' : guild.id }))
                if len(entries) == 0:
                    continue

                for entry in entries:
                    due_at = arrow.get(entry['due_at']).timestamp()
                    if arrow.now().timestamp() < due_at:
                        continue

                    # Sleep to yield db remove
                    await asyncio.sleep(0.1)
                    logger.debug(f'Executing reminder id {entry.doc_id} | due_at = {due_at}  now = {arrow.now().timestamp()}')

                    data = entry.copy()
                    table.remove(doc_ids=[ entry.doc_id ])

                    channel = guild.get_channel(data['channel_id'])
                    if isinstance(channel, type(None)):
                        channel = await guild.fetch_channel(data['channel_id'])
                        if isinstance(channel, type(None)):
                            logger.debug(f'Channel id {data["channel_id"]} in server {guild.name} does not exist\n')
                            continue

                    user = guild.get_member(data['user_id'])
                    if isinstance(user, type(None)):
                        user = await guild.fetch_member(data['user_id'])
                        if isinstance(user, type(None)):
                            logger.debug(f'User id {data["user_id"]} in server {guild.name} does not exist\n')
                            continue

                    embed = discord.Embed(color=0x1ABC9C, timestamp=arrow.get(data['created_at']).datetime)
                    embed.set_author(name=user.name, icon_url=user.avatar.url)
                    embed.add_field(name='⏰ Reminder Message', value=f"```\n{data['text']}\n```")
                    await channel.send(user.mention, embed=embed)
