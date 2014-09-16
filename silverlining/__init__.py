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
    print(e)
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
    print(e)
    sys.stdout.write(
        "Unable to connect to SoundCloud. Check your config.json or network connection.\n"
    )
    sys.exit(1)


from silverlining import utils
from silverlining import models
from silverlining import vlc
from silverlining import commands


@click.command()
@click.argument('cmd', nargs=-1)
def cli(cmd):
    """Main entry point of the script"""
    # Make sure command is long enough
    if len(cmd) == 0:
        sys.stdout.write("no arguments, no service\n")
        return
    elif len(cmd) == 1 and cmd[0] != 'help':
        sys.stdout.write("the only one word command I know is 'help'\n")
        return
    elif len(cmd) == 1 and cmd[0] == 'help':
        sys.stdout.write("but that doesn't mean I'm going to\n")
        return

    # Try parsing the command
    try:
        cmd, args = commands.parse_cli_cmd(cmd)
    except commands.CommandError as e:
        sys.stdout.write("%s\n" % e)
        return

    # Go!
    cmd(*args)
