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

    @staticmethod
    def DiscordCmd(example: str, help: str) -> typing.Callable:

        def wrapper(fn : typing.Callable) -> dict:
            return {
                'func'    : fn,
                'type'    : 'cmd',
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
