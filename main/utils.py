import typing
import functools


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
