"""BotdFactory CLI Interface"""

from __future__ import absolute_import

import argparse
import random
import string
import sys

from twisted.internet import reactor, ssl
from twisted.python import log

from botd import botd


def cli(parser=None):
    """Parse CLI arguments and options."""
    if parser is None:
        parser = argparse.ArgumentParser()
    parser.add_argument(
        "-a",
        "--admin",
        help="Specify an administrator for the bot.",
    )
    parser.add_argument(
        "-k",
        "--key",
        help="Specify a password for administering the bot.",
        default="".join(random.choice(string.ascii_letters) for _ in range(8)),  # nosec
    )
    parser.add_argument(
        "-n",
        "--nick",
        help="Specify a nickname to use.",
        default="botd" + str(random.randint(0, 99999)).zfill(5),  # nosec
    )
    parser.add_argument(
        "-p",
        "--port",
        help="Specify a port number to connect on.",
        default=6697,
    )
    parser.add_argument(
        "-i",
        "--identify",
        help="Specify a password to identify to NickServ with.",
    )
    parser.add_argument(
        "server",
        nargs="?",
        help="Specify a server to connect to.",
        default="chat.freenode.net",
    )
    return parser


def main(args=None):
    """Execute CLI commands."""
    if args is None:
        args = cli().parse_args()
    log.startLogging(sys.stdout)
    reactor.connectSSL(  # pylint: disable=no-member
        host=args.server,
        port=args.port,
        factory=botd.BotdFactory(
            nickname=args.nick,
            key=args.key,
            identify=args.identify,
            admins=[] if args.admin is None else [args.admin],
        ),
        contextFactory=ssl.ClientContextFactory(),
    )
    reactor.run()  # pylint: disable=no-member


if __name__ == "__main__":
    sys.exit(main())
