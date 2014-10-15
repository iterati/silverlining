__title__ = 'silverlining'
__version__ = '0.1'
__author__ = 'John Miller'
__license__ = 'MIT'
__copyright__ = 'Copyright 2014 ' + __author__

import atexit
import os
import simplejson
import sys

# Get settings
DOT_FILES = os.path.expanduser('~/.silverlining')
CONFIG_FILE = os.path.expanduser('~/.silverlining/config.json')
HIST_FILE = os.path.expanduser('~/.silverlining/history.json')

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


from silverlining.base import (
    parse_search_arguments,
    get_search_results,
    get_search_interp,
)
from silverlining.models import (
    Playlist,
    Track,
    User,
)
from silverlining.vlc import (
    Player,
)


@click.command()
@click.argument('cmd', nargs=1, required=False)
@click.argument('args', nargs=-1, required=False)
def cli(cmd=None, args=None):
    """Main entry point of the script"""
    try:
        username, category, query = parse_search_arguments(args)
    except Exception as e:
        sys.stdout.write("%s\n" % e)
        return

    if cmd in ['s', 'search'] or not cmd:
        cli_search(username, category, query)
    elif cmd in ['p', 'play']:
        cli_play(username, category, query)
    else:
        sys.stdout.write("Unrecognized command %s\n" % cmd)

    sys.stdout.write("\n")


def cli_search(username, category, query):
    sys.stdout.write("Searching " + get_search_interp(username, category, query) + "\n")
    items = get_search_results(username, category, query)
    sys.stdout.write(u"\n".join([i.cli_display for i in items]))


def cli_play(username, category, query):
    sys.stdout.write("Playing " + get_search_interp(username, category, query) + "\n")
    items = get_search_results(username, category, query)
    if items:
        if items[0]['kind'] == 'track':
            tracks = items
        else:
            tracks = items[0].tracks

    with Player() as player:
        player.load_tracks(tracks)
        player.run()
