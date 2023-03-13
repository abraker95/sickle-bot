import typing
import functools


class DiscordCmdBase():

    @staticmethod
    def DiscordCmd(example: str, help: str) -> typing.Callable:

        def wrapper(fn : typing.Callable) -> dict:
            return {
                'func'    : fn,
                'example' : example,
                'help'    : help
            }

        return wrapper
