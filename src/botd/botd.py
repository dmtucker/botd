"""Botd and BotdFactory Definitions"""


from passlib.apps import custom_app_context  # type: ignore
from twisted.internet import protocol, reactor
from twisted.python import log
from twisted.words.protocols import irc

from botd.commands import Commands as BotdCommands


class Botd(irc.IRCClient):  # pylint: disable=abstract-method

    """A Python IRC Bot"""

    def __init__(self, nickname, key, identify=None, admins=None):
        self.nickname = nickname
        self.key_hash = None
        self.identify = identify
        self.admins = [] if admins is None else admins
        self.set_key(key)

    def set_key(self, key):
        """Set a new bot key."""
        log.msg(f"The key for {self.nickname} is {key}.")
        self.key_hash = custom_app_context.encrypt(key)

    def authorize(self, user, key=None):
        """Determine if a user and/or key grants permission for admin actions."""
        return (
            user.split("!")[0] in self.admins
            if key is None
            else custom_app_context.verify(key, self.key_hash)
        )

    # Callbacks

    def irc_INVITE(self, prefix, params):  # pylint: disable=invalid-name  # noqa: N802
        """Automatically join channels the bot is invited to."""
        invitee, channel = params
        log.msg(f"{prefix} invites {invitee} to {channel}.")
        self.join(channel)

    # Events

    def joined(self, channel):
        log.msg(f"{self.nickname} joins {channel}.")

    def kickedFrom(self, channel, kicker, message):  # noqa: N802
        log.msg(f"{kicker} kicks {self.nickname} from {channel}.")

    def left(self, channel):
        log.msg(f"{self.nickname} leaves {channel}.")

    def nickChanged(self, nick):  # noqa: N802
        log.msg(f"{self.nickname} becomes {nick}.")
        self.nickname = nick

    def noticed(self, user, channel, message):
        log.msg(
            {
                "*": f"SERVER {user}: {message}",
                self.nickname: f"NOTICE {user}: {message}",
            }.get(channel, f"NOTICE {user} -> {channel}: {message}"),
        )

    def privmsg(self, user, channel, message):
        if channel == self.nickname:
            f = getattr(BotdCommands, message.split()[0], None)
            if f is None:
                log.msg(f"{user}: {message}")
            else:
                f(self, user, channel, message)

    def signedOn(self):  # noqa: N802
        log.msg(f"{self.nickname} signs on to {self.hostname}.")
        self.join("#botd")
        if self.identify is not None:
            log.msg(f"{self.nickname} identifies to NickServ.")
            self.msg("NickServ", f"IDENTIFY {self.identify}")


class BotdFactory(protocol.ClientFactory):

    """Create Botd bots."""

    protocol = Botd  # type: ignore

    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs

    def buildProtocol(self, addr):  # noqa: N802
        return Botd(*self._args, **self._kwargs)

    def clientConnectionLost(self, connector, reason):  # noqa: N802
        log.msg("\n".join(["Connection Lost", str(reason).strip()]))
        connector.connect()

    def clientConnectionFailed(self, connector, reason):  # noqa: N802
        log.msg("\n".join(["Connection Failed", str(reason).strip()]))
        reactor.stop()
