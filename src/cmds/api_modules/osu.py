import discord
import warnings

from core import DiscordBot


class CmdsOsu:

    # Cache for quicker access
    __ot_feed_ch_cache = None

    @staticmethod
    async def post(bot: DiscordBot, data: dict):
        """
        Processes the '/osu/post' BotApi endpoint
        """
        required_keys = set((
                'subforum_id',
                'subforum_name',
                'post_date',
                'prev_post_date',
                'thread_title',
                'post_id',
                'first_post_id',
                'username',
                'user_id',
                'avatar_url',
                'contents',
        ))
        if not required_keys.issubset(data):
            warnings.warn(f'Comment data is incomplete!\nData: {data.keys()}\nRequired: {required_keys}')
            return

        # Embed character limit
        contents = data['contents'][:5700]

        # Field character limit
        chunks = [ contents[i : i + 1023] for i in range(0, len(contents), 1023) ]

        # Get post & user urls
        post_url = f'https://osu.ppy.sh/community/forums/posts/{data["post_id"]}'
        user_url = f'https://osu.ppy.sh/users/{data["user_id"]}'

        # Patch up default avatar link
        if 'avatar-guest' in data['avatar_url']:
            data['avatar_url'] = f'https://osu.ppy.sh/{data["avatar_url"]}'

        # Set color
        color = 0x1abc9c  # Greenish
        if data['post_id'] == data['first_post_id']:
            color = 0xeeeeee  # First post of thread is white

        # Construct embed
        embed = discord.Embed(color=color, title=f'Subforum: {data["subforum_name"]}', description=f'[{data["thread_title"]}]({post_url})\n')
        embed.set_author(name=data['username'], url=user_url)
        embed.set_thumbnail(url=data['avatar_url'])
        for chunk in chunks:
            embed.add_field(name=f'\u200b', value=chunk, inline=True)
        embed.set_footer(text=data['post_date'])

        # Send
        is_debug = DiscordBot.get_cfg('Core', 'is_debug')
        ot_feed_channel = 'debug-ot-feed' if is_debug else 'ot-feed'

        try:
            # If channel is cached
            if not isinstance(CmdsOsu.__ot_feed_ch_cache, type(None)):
                await CmdsOsu.__ot_feed_ch_cache.send(embed=embed)
                return

            # Otherwise look for it
            for server in bot.guilds:
                for channel in server.channels:
                    if channel.name == ot_feed_channel:
                        CmdsOsu.__ot_feed_ch_cache = channel
                        await channel.send(embed=embed)
                        return
        except discord.errors.Forbidden as e:
            warnings.warn(f'Error posting forum post to channel {channel.name}: {e}')
        except discord.errors.HTTPException as e:
            warnings.warn(f'Error posting forum post: {e} | Contents:\n{contents}')
        except Exception as e:
            warnings.warn(
                f'Unable to send message to #"{ot_feed_channel}";\n'
                f'{data}\n'
                f'{e}\n'
            )
            return

        warnings.warn(f'No #"{ot_feed_channel}" channel found!')
