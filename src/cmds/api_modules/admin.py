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
            'src',
            'contents',
        ))
        if not required_keys.issubset(data):
            warnings.warn(
                f'Data is incomplete!\n'
                f'Data: {data.keys()}\n'
                f'Required: {required_keys}'
            )
            return

        channel_id = DiscordBot.get_cfg('Core', 'debug_channel_id')

        # Embed character limit
        contents = data['contents'][:5700]

        # Field character limit
        chunks = [ contents[i : i + 1023] for i in range(0, len(contents), 1023) ]
        for chunk in chunks:
            try:
                await bot.get_channel(channel_id).send(chunk)
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
