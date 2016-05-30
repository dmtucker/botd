"""Botd IRC Interface"""

from __future__ import absolute_import

from functools import wraps
import inspect
import textwrap

from twisted.internet import reactor
from twisted.python import log


def argv_length(minimum=0, maximum=None):
    """Create a decorator that checks for an appropriate number of args in the message."""
    def decorator(func):
        """Decorate functions that expect args in the message."""
        @wraps(func)
        def decorated(cls, bot, user, channel, message):
            """Call the function if the expected number of arguments were provided."""
            argv = message.split(' ')
            if maximum is None:
                maximum = len(argv)
            if minimum <= len(argv) <= maximum:
                func(cls, bot, user, channel, message)
            else:
                bot.msg(user.split('!')[0], textwrap.dedent(func.__doc__).strip())
        return decorated
    return decorator


def require_authorization(key_index=None):
    """Create a decorator that checks for authorization."""
    def decorator(func):
        """Decorate functions that require authorization."""
        @wraps(func)
        def decorated(cls, bot, user, channel, message):
            """Call the function if the user is authorized."""
            argv = message.split(' ')
            key = None if key_index is None or key_index < len(argv) else argv[key_index]
            if bot.authorize(user, key):
                func(cls, bot, user, channel, message)
            else:
                msg = '{0} is not authorized.'.format(user)
                log.msg(msg)
                bot.msg(user.split('!')[0], msg)
        return decorated
    return decorator


# pylint: disable=unused-argument
class Commands(object):

    """Methods Invocable via IRC"""

    @classmethod
    @argv_length(minimum=1, maximum=1)
    def admins(cls, bot, user, channel, message):
        """
        usage: admins
        List the bot admins.
        """
        bot.msg(user.split('!')[0], ', '.join(bot.admins))

    @classmethod
    @argv_length(minimum=2, maximum=2)
    @require_authorization()
    def key(cls, bot, user, channel, message):
        """
        usage: key {key}
        Set a new bot key.
        """
        bot.set_key(message.split(' ')[1])

    @classmethod
    @argv_length(minimum=2, maximum=3)
    @require_authorization(key_index=2)
    def join(cls, bot, user, channel, message):
        """
        usage: join {channel} [{key}]
        Join a channel.
        """
        bot.join(message.split(' ')[1])

    @classmethod
    @argv_length(minimum=2, maximum=3)
    @require_authorization(key_index=2)
    def leave(cls, bot, user, channel, message):
        """
        usage: leave {channel} [{key}]
        Leave a channel.
        """
        bot.leave(message.split(' ')[1])

    @classmethod
    @argv_length(minimum=1, maximum=2)
    @require_authorization(key_index=1)
    def stop(cls, bot, user, channel, message):
        """
        usage: stop [{key}]
        Stop running.
        """
        reactor.stop()

    @classmethod
    def help(cls, bot, user, channel, message):
        """
        usage: help {command}
        Show helpful information.
        """
        lines = []
        commands = message.split()[1:]
        if len(commands) == 1:
            command = commands[0]
            func = getattr(cls, command, None)
            lines.append(
                'Invalid Command: {0}'.format(command)
                if func is None else
                textwrap.dedent(func.__doc__).strip()
            )
        bot.msg(
            user.split('!')[0],
            '\n'.join(lines)
            if len(lines) > 0 else
            textwrap.dedent(
                cls.help.__doc__.format(
                    command='({0})'.format(
                        '|'.join([
                            name for name, _ in inspect.getmembers(cls, predicate=inspect.ismethod)
                        ]),
                    ),
                ),
            ).strip()
        )
