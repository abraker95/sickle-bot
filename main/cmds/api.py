import warnings

from main import DiscordCmdBase, DiscordBot
from main.FeedServer import FeedServer

from api.osu import CmdsOsu
from api.admin import CmdsAdmin


class BotApi:
    """
    Command access for this bot: [external] -> DiscordBot
    """

    @DiscordCmdBase.DiscordEvent()
    async def api_server(self: DiscordBot):
        await FeedServer.init(lambda route, data: BotApi.__handle_data(self, route, data))


    @staticmethod
    async def __handle_data(bot: DiscordBot, endpoint: str, data: dict):
        """
        Forwards to a DiscordBot capable destination based on what the BotApi endpoint is
        """
        match endpoint:
            case '/osu/post':   await CmdsOsu.post(bot, data)
            case '/admin/post': await CmdsAdmin.post(bot, data)
            case _:
                warnings.warn(f'Invalid BotApi endpoint: "{endpoint}"')
