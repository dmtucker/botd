"""BotdFactory CLI Interface"""

from __future__ import absolute_import

import argparse
import random
import string
import sys

from twisted.internet import reactor, ssl
from twisted.python import log

from botd import botd


def cli(parser=argparse.ArgumentParser()):
    """Parse CLI arguments and options."""
    parser.add_argument(
        '-a', '--admin',
        help='Specify an administrator for the bot.',
    )
    parser.add_argument(
        '-k', '--key',
        help='Specify a password for administering the bot.',
        default=''.join(random.choice(string.ascii_letters) for _ in range(8)),
    )
    parser.add_argument(
        '-n', '--nick',
        help='Specify a nickname to use.',
        default='botd{0:05}'.format(random.randint(0, 99999)),
    )
    parser.add_argument(
        '-p', '--port',
        help='Specify a port number to connect on.',
        default=6697,
    )
    parser.add_argument(
        '-i', '--identify',
        help='Specify a password to identify to NickServ with.',
    )
    parser.add_argument(
        'server',
        nargs='?',
        help='Specify a server to connect to.',
        default='chat.freenode.net',
    )
    return parser


def main(args=cli().parse_args()):
    """Execute CLI commands."""
    log.startLogging(sys.stdout)
    reactor.connectSSL(
        host=args.server,
        port=args.port,
        factory=botd.BotdFactory(
            nickname=args.nick,
            key=args.key,
            identify=args.identify,
            admins=[] if args.admin is None else [args.admin]
        ),
        contextFactory=ssl.ClientContextFactory(),
    )
    reactor.run()


if __name__ == '__main__':
    sys.exit(main())
