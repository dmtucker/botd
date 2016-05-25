import argparse
import sys
import ConfigParser
from twisted.internet import reactor
from twisted.python import log

import botd


def main():
    if len(sys.argv) < 2:
        print('usage: '+sys.argv[0]+' [configfile ...]')
    log.startLogging(sys.stdout)
    for cfgfile in sys.argv[1:]:
        config = ConfigParser.ConfigParser()
        log.msg('Reading '+cfgfile+'... ')
        log.msg('done' if config.read(cfgfile) == [cfgfile] else 'fail')
        # TODO log.startLogging(open(cfgfile+'.log', 'w'))
        reactor.connectTCP(
            host=config.get('connection', 'server'),
            port=int(config.get('connection', 'port')),
            factory=botd.BotFactory(config)
        )
        config = None
    reactor.run()


if __name__ == '__main__':
    sys.exit(main())
