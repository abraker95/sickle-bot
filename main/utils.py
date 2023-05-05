import typing
import traceback


class Utils():

    @staticmethod
    def format_exception(ex: Exception):
        frames = traceback.extract_tb(ex.__traceback__)

        err = f'Raised {type(ex)}: {ex}\n'
        for frame in frames:
            file = frame.filename.split('\\')[-1]
            err += f'  {file}, line {frame.lineno} in {frame.name}\n'
        err += f'    {frames[-1].line}'

        return err


class DiscordCmdBase():

    ADMINISTRATOR = 0  # Only admin can use
    MODERATOR     = 1  # Designated moderator command
    CONDITIONAL   = 2  # x - Command can be used only if x is true
    ANYONE        = 3  # Anyone can use the command

    @staticmethod
    def DiscordCmd(perm: int, example: str, help: str) -> typing.Callable:
        # TODO: Add built-in permissions
        #   - DiscordCmdBase.ADMIN - Only admin can use
        #   - DiscordCmdBase.PERM([ x0, x1, ... ]) - Command requires permissions x0, x1, etc
        #   - DiscordCmdBase.COND(x) - Command can be used only if x is true
        #   - DiscordCmdBase.NONE - Anyone can use the command

        def wrapper(fn : typing.Callable) -> dict:
            return {
                'func'    : fn,
                'type'    : 'cmd',
                'perm'    : perm,
                'example' : example,
                'help'    : help
            }

        return wrapper


    @staticmethod
    def DiscordEvent() -> typing.Callable:

        def wrapper(fn : typing.Callable) -> dict:
            return {
                'func'    : fn,
                'type'    : 'event',
                'example' : '',
                'help'    : ''
            }

        return wrapper
