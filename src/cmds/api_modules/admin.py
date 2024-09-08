import discord
import warnings

from core import DiscordBot


class CmdsAdmin:

    @staticmethod
    async def post(bot: DiscordBot, data: dict):
        """
        Processes the '/admin/post' BotApi endpoint
        """
        required_keys = set((
            'contents',
            'src'
        ))
        if not required_keys.issubset(data):
            warnings.warn(f'Data is incomplete!\nData: {data.keys()}\nRequired: {required_keys}')
            return

        # Embed character limit
        contents = data['contents'][:5700]

        # Field character limit
        chunks = [ contents[i : i + 1023] for i in range(0, len(contents), 1023) ]

        # Set color
        color = 0x1abc9c  # Greenish

        # Construct embed
        embed = discord.Embed(color=color, title=f'Source: {data["src"]}')
        for chunk in chunks:
            embed.add_field(name=f'\u200b', value=chunk, inline=True)

        # Send
        channel_id = DiscordBot.get_cfg('Core', 'debug_channel_id')

        try:
            await bot.get_channel(channel_id).send(embed=embed)
            return
        except discord.errors.Forbidden as e:
            warnings.warn(f'Error posting forum post to admin channel ID {channel_id}: {e}')
        except discord.errors.HTTPException as e:
            warnings.warn(f'Error posting forum post: {e} | Contents:\n{contents}')
        except Exception as e:
            warnings.warn(
                f'Unable to send message to admin ch id "{channel_id}";\n'
                f'{data}\n'
                f'{e}\n'
            )
            return

        warnings.warn(f'No admin by id "{channel_id}" found!')
