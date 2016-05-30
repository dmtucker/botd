"""Botd IRC Interface"""

from __future__ import absolute_import

from functools import wraps
import inspect
import textwrap

from twisted.internet import reactor


def argv_length(minimum, maximum):
    """Create a decorator that checks for an appropriate number of args in the message."""
    def decorator(func):
        """Decorate functions that expect args in the message."""
        @wraps(func)
        def decorated(cls, bot, user, channel, message):
            """Call the function if the expected number of arguments were provided."""
            argv = message.split(' ')
            if minimum <= len(argv) <= maximum:
                func(cls, bot, user, channel, message)
            else:
                bot.msg(user.split('!')[0], textwrap.dedent(func.__doc__).strip())
        return decorated
    return decorator


def require_authorization(key_index=None):
    """Create a decorator that checks for authorization."""
    def decorator(func, key_index=key_index):
        """Decorate functions that require authorization."""
        @wraps(func)
        def decorated(
                cls,
                bot,
                user,
                channel,
                message,
                key_index=key_index,
        ):  # pylint: disable=too-many-arguments
            """Call the function if the user is authorized."""
            argv = message.split(' ')
            key = argv[key_index] if key_index is not None and key_index < len(argv) else None
            if bot.authorize(user, key):
                func(cls, bot, user, channel, message)
            else:
                bot.msg(
                    user.split('!')[0],
                    '{0} is not authorized.'.format(user)
                    if key is None else
                    'Incorrect Key: {0}'.format(key),
                )
        return decorated
    return decorator


# pylint: disable=unused-argument
class Commands(object):

    """Methods Invocable via IRC"""

    @classmethod
    @argv_length(1, 1)
    def admins(cls, bot, user, channel, message):
        """
        usage: admins
        List the bot admins.
        """
        bot.msg(user.split('!')[0], ', '.join(bot.admins))

    @classmethod
    @argv_length(2, 2)
    @require_authorization()
    def key(cls, bot, user, channel, message):
        """
        usage: key {key}
        Set a new bot key.
        """
        bot.set_key(message.split(' ')[1])

    @classmethod
    @argv_length(2, 3)
    @require_authorization(key_index=2)
    def join(cls, bot, user, channel, message):
        """
        usage: join {channel} [{key}]
        Join a channel.
        """
        bot.join(message.split(' ')[1])

    @classmethod
    @argv_length(2, 3)
    @require_authorization(key_index=2)
    def leave(cls, bot, user, channel, message):
        """
        usage: leave {channel} [{key}]
        Leave a channel.
        """
        bot.leave(message.split(' ')[1])

    @classmethod
    @argv_length(1, 2)
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
