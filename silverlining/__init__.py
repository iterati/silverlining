__title__ = 'silverlining'
__version__ = '0.1'
__author__ = 'John Miller'
__license__ = 'MIT'
__copyright__ = 'Copyright 2014 ' + __author__

import os
import simplejson
import sys

# Get settings
DOT_FILES = os.path.expanduser('~/.silverlining')
CONFIG_FILE = os.path.join(DOT_FILES, 'config.json')

try:
    with open(CONFIG_FILE, 'rb') as f:
        config = f.read()
        config = simplejson.loads(config)

        CLIENT_ID = config['client_id']
        SECRET_KEY = config['secret_key']
        USERNAME = config['username']
        PASSWORD = config['password']

except Exception as e:
    if not os.path.isdir(DOT_FILES):
        os.mkdir(DOT_FILES)

    if not os.path.isfile(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as f:
            f.write(simplejson.dumps(
                {'client_id': '', 'secret_key': '', 'username': '', 'password': ''},
                indent=2,
            ))

    sys.stdout.write(
        "Need to enter your api and login credentials for SoundCloud.\n"
        "Please edit %s.\n\n" % CONFIG_FILE +
        "If you need to sign up for an API key, please visit "
        "http://soundcloud.com/you/apps and create an app.\n"
    )
    sys.exit(1)

import click
import soundcloud


# Try to connect to SoundCloud API
try:
    client = soundcloud.Client(
        client_id=CLIENT_ID,
        client_secret=SECRET_KEY,
        username=USERNAME,
        password=PASSWORD,
    )
except Exception as e:
    sys.stdout.write(
        "Unable to connect to SoundCloud. Check your config.json or network connection.\n"
    )
    sys.exit(1)


from silverlining import utils
from silverlining import models
from silverlining import vlc
# from silverlining import commands


@click.command()
@click.argument('cmd', nargs=1, required=False)
@click.argument('args', nargs=-1, required=False)
def cli(cmd=None, args=None):
    """Main entry point of the script"""
    if cmd in ['h', 'help']:
        cli_help(args)
    elif cmd in ['s', 'search'] or not cmd:
        cli_search(args)
    elif cmd in ['p', 'play']:
        cli_play(args)
    else:
        sys.stdout.write("Unrecognized command %s\n" % cmd)


def cli_help(args):
    if not args:
        sys.stdout.write("help\n")
    elif args[0] in ['s', 'search']:
        sys.stdout.write("help search\n")
    elif args[0] in ['p', 'play']:
        sys.stdout.write("help play\n")
    else:
        sys.stdout.write("no help for %s\n" % args[0])


def parse_cli_arguments(args):
    if not args:
        return None, 'stream', None
    if args[0] in ['me', 'stream']:
        if len(args) > 1:
            return None, 'stream', args[1]
        return None, 'stream', None
    elif args[0] in ['t', 'track', 'tracks']:
        if len(args) > 1:
            return None, 'track', args[1]
        raise Exception("not enough arguments")
    elif args[0] in ['p', 'playlist', 'playlists']:
        if len(args) > 1:
            return None, 'playlist', args[1]
        raise Exception("not enough arguments")
    else:
        if len(args) == 1:
            return args[0], 'user', None
        elif args[1] in ['t', 'track', 'tracks']:
            if len(args) > 2:
                return args[0], 'track', args[2]
            return args[0], 'track', None
        elif args[1] in ['p', 'playlist', 'playlists']:
            if len(args) > 2:
                return args[0], 'playlist', args[2]
            return args[0], 'playlist', None
    raise Exception("unable to parse command %s" % ' '.join(args))


def get_items(username, category, query):
    if category == 'stream':
        items = models.Track.get_from_stream(query)
    elif category == 'user':
        items = models.User.get(username)
    else:
        user = models.User.get_one(username) if username else None
        if category == 'track':
            items = models.Track.get(query, user)
        elif category == 'playlist':
            items = models.Playlist.get(query, user)

    return items


def get_interp(username, category, query):
    interp = ""
    if category == 'stream':
        interp += "your stream"
    elif username:
        interp += "%s's %ss" % (username, category)
    else:
        interp += "%ss" % category
    if query:
        interp += " for %s" % query
    return interp


def cli_search(args):
    try:
        username, category, query = parse_cli_arguments(args)
    except Exception as e:
        sys.stdout.write("%s\n" % e)
        return

    sys.stdout.write("Searching " + get_interp(username, category, query) + "\n")
    items = get_items(username, category, query)
    sys.stdout.write(u"\n".join([i.cli_display for i in items]) + "\n\n")


def cli_play(args):
    try:
        username, category, query = parse_cli_arguments(args)
    except Exception as e:
        sys.stdout.write("%s\n" % e)
        return

    sys.stdout.write("Playing " + get_interp(username, category, query) + "\n")
    items = get_items(username, category, query)
    if items:
        if items[0]['kind'] == 'track':
            tracks = items
        else:
            tracks = items[0].tracks

    with vlc.player:
        vlc.player.load_tracks(tracks)
        vlc.player.run()

    sys.stdout.write("\n\n")
