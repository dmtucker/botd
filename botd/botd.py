"""Botd and BotdFactory Definitions"""

from __future__ import absolute_import

from passlib.apps import custom_app_context
from twisted.internet import protocol, reactor
from twisted.python import log
from twisted.words.protocols import irc

from botd.commands import Commands as BotdCommands


class Botd(irc.IRCClient):

    """A Python IRC Bot"""

    def __init__(self, nickname, key, identify=None, admins=None):
        self.nickname = nickname
        self.key_hash = None
        self.identify = identify
        self.admins = [] if admins is None else admins
        self.set_key(key)

    def set_key(self, key):
        """Set a new bot key."""
        log.msg('The key for {0} is {1}'.format(self.nickname, key))
        self.key_hash = custom_app_context.encrypt(key)

    def authorize(self, user, key=None):
        """Determine if a user or key grants permission for administrative actions."""
        return (
            user.split('!')[0] in self.admins
            if key is None else
            custom_app_context.verify(key, self.key_hash)
        )

    # Callbacks

    def irc_INVITE(self, prefix, params):  # pylint: disable=invalid-name
        """Automatically join channels the bot is invited to."""
        invitee, channel = params
        log.msg('{0} invites {1} to {2}.'.format(prefix, invitee, channel))
        self.join(channel)

    # Events

    def joined(self, channel):
        log.msg('{0} joins {1}.'.format(self.nickname, channel))

    def kickedFrom(self, channel, kicker, message):
        log.msg('{0} kicks {1} from {2}.'.format(kicker, self.nickname, channel))

    def left(self, channel):
        log.msg('{0} leaves {1}.'.format(self.nickname, channel))

    def nickChanged(self, nick):
        log.msg('{0} becomes {1}.'.format(self.nickname, nick))
        self.nickname = nick

    def noticed(self, user, channel, message):
        log.msg(
            {
                '*': 'SERVER {0}: {1}'.format(user, message),
                self.nickname: 'NOTICE {0}: {1}'.format(user, message),
            }.get(
                channel,
                'NOTICE {0} -> {1}: {2}'.format(user, channel, message)
            )
        )

    def privmsg(self, user, channel, message):
        if channel == self.nickname:
            f = getattr(BotdCommands, message.split()[0], None)
            if f is None:
                log.msg('{0}: {1}'.format(user, message))
            else:
                f(self, user, channel, message)

    def signedOn(self):
        log.msg('{0} signs on to {1}.'.format(self.nickname, self.hostname))
        self.join('#botd')
        if self.identify is not None:
            log.msg('{0} identifies to NickServ.'.format(self.nickname))
            self.msg('NickServ', 'IDENTIFY {0}'.format(self.identify))


class BotdFactory(protocol.ClientFactory):

    """Create Botd bots."""

    protocol = Botd

    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs

    def buildProtocol(self, addr):
        return Botd(*self._args, **self._kwargs)

    def clientConnectionLost(self, connector, reason):
        log.msg('\n'.join(['Connection Lost', str(reason).strip()]))
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        log.msg('\n'.join(['Connection Failed', str(reason).strip()]))
        reactor.stop()
