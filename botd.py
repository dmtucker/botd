#!/usr/bin/env python

import sys
import hashlib
import json
import requests
import feedparser
import ConfigParser
from datetime import datetime
from difflib import SequenceMatcher
from lxml.html import clean
from threading import Timer
from time import sleep
from twisted.python import log
from twisted.internet import reactor, protocol
from twisted.words.protocols import irc
from twython import Twython

__version__ = '0.1.0b'


def shortened_url(url):
    return json.loads(
        requests.post(
            'https://www.googleapis.com/urlshortener/v1/url',
            headers={
                'content-type': 'application/json',
            },
            data=json.dumps({
                'longUrl': url,
            })
        ).text
    ).get('id')


# http://stackoverflow.com/questions/17388213/python-string-similarity-with-probability
def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


def _strip_html(html):
    return clean.Cleaner(
        allow_tags=[''],
        remove_unknown_tags=False
    ).clean_html(html)


def _sanitized(text):
    return ' '.join(
        _strip_html(text)
        .replace('<div>', '').replace('</div>', '')  # This is to handle a bug in lxml.
        .replace('\n', ' ').split()
    )


def _sanitized_entry(entry):
    entry.description = _sanitized(entry.description)
    if not entry.description:
        return None
    description = entry.description
    if len(description) > 140:
        description = description[:140]+'...'
    link = shortened_url(entry.link)
    if link is not None:
        description += ' ['+link+']'
    return description+' ['+entry.published+']'


def _format_rss_message(title, feed, result):
    msg = '['+title+'] '
    if similar(title.lower(), feed.title.lower()) < 0.5: 
        msg += feed.title+': '
    msg += result
    return msg


def timestamp():
    return datetime.now().isoformat()


def user2nick(user):
    return user.split('!')[0]


# http://stackoverflow.com/questions/3393612/run-certain-code-every-n-seconds
class RepeatedTimer(object):

    def __init__(self, interval, function, *args, **kwargs):
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False


class Botd(irc.IRCClient):

    _rss_latest_ids = {}
    _twitter_latest_id = 0

    def _get_rss_feeds(self):
        rss_feeds = []
        feeds = self.factory.config.get('rss', 'feeds').split('\n')
        if len(feeds) > 0 and feeds[0] == '':
            feeds = feeds[1:]
        title = None
        for i in range(len(feeds)):
            if i%2 == 1:
                rss_feeds.append((feeds[i-1], feeds[i]))
        return rss_feeds

    def poll_rss(self):
        results = []
        remaining = int(self.factory.config.get('rss', 'feed_max_items'))*len(self._get_rss_feeds())
        for title, feed in self._get_rss_feeds():
            items = feedparser.parse(feed)
            if self._rss_latest_ids.get(feed) is None:
                if len(items.entries) != 0:
                    entry = items.entries[0]
                    if not hasattr(entry, 'id'):
                        entry.id = hashlib.md5(
                            entry.description.encode('ascii', 'ignore')
                        ).hexdigest()
                    self._rss_latest_ids[feed] = entry.id
                    result = _sanitized_entry(entry)
                    if result:
                        results += [_format_rss_message(title, items.feed, result)]
                continue
            feed_remaining = int(self.factory.config.get('rss', 'feed_max_items'))
            new_latest_id = None
            for entry in items.entries:
                if not hasattr(entry, 'id'):
                    entry.id = hashlib.md5(
                        entry.description.encode('ascii', 'ignore')
                    ).hexdigest()
                if new_latest_id is None:
                    new_latest_id = entry.id
                if entry.id == self._rss_latest_ids.get(feed):
                    self._rss_latest_ids[feed] = new_latest_id
                    break
                result = _sanitized_entry(entry)
                if result:
                    results += [_format_rss_message(title, items.feed, result)]
                remaining -= 1
                feed_remaining -= 1
                if remaining < 1:
                    self._rss_latest_ids[feed] = new_latest_id
                    return results
                elif feed_remaining < 1:
                    self._rss_latest_ids[feed] = new_latest_id
                    break
        return results

    def poll_twitter(self):
        api = Twython(
            self.factory.config.get('twitter', 'key'),
            access_token=self.factory.config.get('twitter', 'token')
        )
        tweets = api.search(
            q=self.factory.config.get('twitter', 'query')+' -filter:retweets',
            lang='en',
            count=1 if self._twitter_latest_id == 0 else 100,
            result_type='recent',
            since_id=self._twitter_latest_id
        )
        self._twitter_latest_id = max(
            self._twitter_latest_id,
            tweets.get('search_metadata', {}).get('max_id')
        )
        results = []
        for tweet in tweets["statuses"]:
            if tweet.get('possibly_sensitive'):
                log.msg('sensitive tweet... skipping', file=sys.stderr)  # TODO DEBUG
                continue
            text = _sanitized(tweet.get('text'))
            name = tweet.get('user', {}).get('name')
            user = tweet.get('user', {}).get('screen_name')
            time = tweet.get('created_at')
            # The following code is commented because %z is not supported for now.
            #time = datetime.strptime(time, '%a %b %d %H:%M:%S %z %Y')
            #time = time.strftime('%Y-%m-%d %H:%M:%S')
            msg = '[Twitter] @'+user
            if similar(user, name) < 0.5: 
                msg += ' ('+name+')'
            msg += ': '+text
            msg += ' ['+time+']'
            results += [msg]
        return results

    def poll(self):
        """
        TODO
        :return:
        """
        log.msg('poll')
        for f in self.sources:
            self.send2subscribers(f())

    def authorized(self, key):
        """ TODO """
        try:
            return hashlib.md5(str(key)).hexdigest() == self.factory.key
        except:
            return False

    def subscribers(self, add=(), remove=(), replace=None):
        """ TODO """
        if replace:
            self.factory.subscribers = replace
        for addend in add:
            if addend in self.factory.subscribers:
                continue
            self.factory.subscribers.append(addend)
        for subtrahend in remove:
            if subtrahend not in self.factory.subscribers:
                continue
            self.factory.subscribers.remove(subtrahend)
        return self.factory.subscribers

    def _nickname(self):
        return self.factory.nickname

    nickname = property(_nickname)  # TODO
    timer = None

    ############################################################################

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        log.msg('signedOn')
        for subscriber in self.subscribers():
            if subscriber[0] == '#':
                self.join(subscriber)
        self.timer = RepeatedTimer(
            float(self.factory.config.get('botd', 'polling_interval')),
            self.poll
        )
        self.sources = []
        if self.factory.config.has_section('rss'):
            self.sources.append(self.poll_rss)
        if self.factory.config.has_section('twitter'):
            self.sources.append(self.poll_twitter)
        if self.nickname != self.factory.nickname:
            # TODO nick_ happened.
            pass

    def joined(self, channel):
        """ TODO """
        log.msg('joined: '+channel)
        self.send(channel, ['Hello '+channel+'!'])

    def privmsg(self, user, channel, request):
        """ This will get called when the bot receives a message. """
        log.msg('privmsg: ['+user+' -> '+channel+'] '+request)
        if channel == self.nickname:
            f = getattr(self.__class__, request.split()[0], None)
            if f is not None:
                self.send(
                    user2nick(user),
                    f(self, user, channel, request) or []
                )

    ############################################################################

    def send(self, recipient, messages):
        """ TODO """
        count = 0
        for message in messages:
            self.msg(recipient, message.encode('ascii', 'ignore'))
            count += 1
            sleep(float(self.factory.config.get('botd', 'message_interval')))
            if count == int(self.factory.config.get('botd', 'message_capacity')):
                sleep(float(self.factory.config.get('botd', 'message_interval'))*int(self.factory.config.get('botd', 'message_capacity')))
                count = 0

    def send2subscribers(self, messages):
        """
        TODO
        :param messages:
        :return:
        """
        for message in messages:
            for subscriber in self.subscribers():
                self.send(subscriber, [message])

    ############################################################################

    def version(self, user, channel, request):
        """ Show the version. """
        request = request.split()
        if len(request) != 1:
            return ['TODO']  # TODO
        global __version__
        return [str(__version__)]

    def help(self, user, channel, request):
        """ Show helpful information. """
        cmds = {
            'version':  'usage: version',
            'help':     'usage: help [<command>]',
            'status':   'usage: status',
            'start':    'usage: start <key>',
            'stop':     'usage: stop <key>',
            'add':      'usage: add [<nick> <key>]',
            'drop':     'usage: drop [<nick> <key>]',
        }
        request = request.split()
        if len(request) == 1:
            return ['I understand the following commands: ' +\
                    ', '.join(sorted(cmds.keys()))+'.']
        if len(request) != 2:
            return ['TODO']  # TODO
        cmd = str(request[1]).lower()
        if cmd in cmds.keys():
            return [cmds[cmd], getattr(self.__class__, cmd).__doc__]
        else:
            return ['TODO']  # TODO

    def status(self, user, channel, request):
        """ Show the current running state. """
        request = request.split()
        if len(request) != 1:
            return ['TODO']  # TODO
        response = []
        response.append(
            'I am running.' if self.timer.is_running else 'I am not running.'
        )
        response.append(
            'You are subscribed.' if user2nick(user) in self.subscribers()
            else 'You are not subscribed.'
        )
        response.append('subscribers: '+' '.join(self.subscribers()))  # TODO Is this a good idea?
        return response

    def start(self, user, channel, request):
        """ Start providing status updates. """
        request = request.split()
        if len(request) != 2:
            return ['TODO']  # TODO
        elif self.timer.is_running:
            return ['I am already running.']
        elif self.authorized(request[1]):
            self.timer.start()
            return ['I am now running.']
        else:
            return ['Incorrect Key']

    def stop(self, user, channel, request):
        """ Stop providing status updates. """
        request = request.split()
        if len(request) != 2:
            return ['TODO']  # TODO
        elif self.authorized(request[1]):
            if self.timer.is_running:
                self.timer.stop()
                return ['I am now idling.']
            else:
                self.timer.stop()
                self.quit()
                reactor.stop()
                return ['Goodbye']
        else:
            return ['Incorrect Key']

    def add(self, user, channel, request):
        """ Subscribe. """
        request = request.split()
        subscriber = None
        if len(request) == 1:
            subscriber = user2nick(user)
        elif len(request) == 3:
            subscriber = request[1]
            if not self.authorized(request[2]):
                return ['Incorrect Key']
        else:
            return ['TODO']  # TODO
        if subscriber in self.subscribers():
            return [subscriber+' is already subscribed.']
        if subscriber[0] == '#':
            self.join(subscriber)
        self.subscribers(add=[subscriber])
        return [subscriber+' is now subscribed.']

    def drop(self, user, channel, request):
        """ Unsubscribe. """
        request = request.split()
        subscriber = None
        if len(request) == 1:
            subscriber = user2nick(user)
        elif len(request) == 3:
            subscriber = request[1]
            if not self.authorized(request[2]):
                return ['Incorrect Key']
        else:
            return ['TODO']  # TODO
        if subscriber not in self.subscribers():
            return [subscriber+' is already unsubscribed.']
        self.subscribers(remove=[subscriber])
        if subscriber[0] == '#':
            self.leave(subscriber, 'unsubscribed')
        return [subscriber+' is now unsubscribed.']


class BotFactory(protocol.ClientFactory):

    protocol = Botd

    def __init__(self, config):
        self.config = config
        self.key = hashlib.md5(config.get('session', 'key')).hexdigest()
        self.nickname = str(config.get('irc', 'nick'))
        self.subscribers = config.get('irc', 'subscribers').split() or ['#'+self.nickname]

    #def clientConnectionLost(self, connector, reason):
    #    """If we get disconnected, reconnect to server."""
    #    log.msg('clientConnectionLost: '+str(reason))
    #    connector.connect()

    #def clientConnectionFailed(self, connector, reason):
    #    log.msg('clientConnectionFailed: '+str(reason))
    #    reactor.stop()


if __name__ == '__main__':
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
            factory=BotFactory(config)
        )
        config = None
    reactor.run()
