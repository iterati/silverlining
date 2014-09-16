import functools
import shlex
import sys

from silverlining import (
    models,
    utils,
    vlc,
)


COMMANDS = {}
CATEGORIES = {
    'track': 'track',
    'tracks': 'track',
    't': 'track',
    'ts': 'track',
    'playlist': 'playlist',
    'playlists': 'playlist',
    'p': 'playlist',
    'ps': 'playlist',
    'user': 'user',
}


class CommandError(Exception):
    pass


def command(abbrs, parser):
    def decorator(func):
        COMMANDS[func.__name__] = (func, parser)
        for abbr in abbrs:
            COMMANDS[abbr] = func.__name__

        return func
    return decorator


def parse_cmd(args):
    args = list(args)
    cmd = args.pop(0)

    if cmd not in COMMANDS:
        raise CommandError("Command not recognized.")

    if isinstance(COMMANDS[cmd], str):
        cmd = COMMANDS[cmd]

    cmd, parser = COMMANDS[cmd]
    return cmd, parser(args)


def parse_cmd_string(args_string):
    args = shlex.split(args_string)
    cmd, args = parse_cmd(args)
    if cmd == search:
        args = [cmd(*args)]
        cmd = cli_search
    elif cmd == play:
        args = [cmd(*args)]
        cmd = cli_play
    return cmd, args


def parse_cli_cmd(cmd):
    cmd, args = parse_cmd(cmd)
    if cmd == search:
        args = [cmd(*args)]
        cmd = cli_search
    elif cmd == play:
        args = [cmd(*args)]
        cmd = cli_play
    else:
        raise CommandError("Only search and play are allowed from command line")
    return cmd, args


def _parse_single_arg(args):
    return args[:1]


def _parse_username_category_title(args):
    if len(args) == 0:
        raise CommandError("no arguments")

    if args[0] in CATEGORIES:
        if len(args) == 1:
            raise CommandError("can't only query category")
        elif len(args) == 2:
            (category, title), username = args, None
        else:
            category, username, title = args[:3]
    else:
        if len(args) == 1:
            username, category, title = args[0], 'user', None
        elif len(args) == 2:
            (username, category), title = args, None
        else:
            username, category, title = args

    if category not in CATEGORIES:
        raise CommandError("unrecognized category %s" % category)

    return username, CATEGORIES[category], title


@command(['j'], _parse_single_arg)
def jump(target):
    track = vlc.player.get_track(target)
    if not track:
        return "Track not found"

    vlc.player.jump(track.plid)
    return "Jumping to %s" % track


@command(['s'], _parse_username_category_title)
def search(username, category, title):
    if category == 'user':
        sys.stdout.write("Searching for users like %s.\n" % username)
        items = models.User.get(username)
    else:
        user = models.User.get_one(username) if username else None

        sys.stdout.write("Searching for %ss" % category)
        if user:
            sys.stdout.write(" by %s" % user['username'])
        if title:
            sys.stdout.write(" with title like %s" % title)
        sys.stdout.write(".\n")

        if category == 'track':
            items = models.Track.get(title, user)
        elif category == 'playlist':
            items = models.Playlist.get(title, user)
    return items


@command(['p'], _parse_username_category_title)
def play(username, category, title):
    user = models.User.get_one(username) if username else None

    if category == 'user':
        sys.stdout.write("Playing tracks by %s.\n" % user['username'])

        tracks = user.tracks
    elif category == 'track':
        if utils.isint(title):
            track = models.Track.get_one(title)
            title = track['title']

        sys.stdout.write("Playing tracks")
        if user:
            sys.stdout.write(" by %s" % user['username'])
        if title:
            sys.stdout.write(" with title like %s" % title)
        sys.stdout.write(".\n")

        tracks = models.Track.get(title, user)
    elif category == 'playlist':
        playlist = models.Playlist.get_one(title, user)

        sys.stdout.write(
            "Playing playlist %s (id: %s) by %s.\n" %
            (playlist['title'], playlist['id'], playlist['user']['username'])
        )

        tracks = playlist.tracks
    return tracks


@command(['a'], _parse_username_category_title)
def append(username, category, title):
    tracks = play(username, category, title)
    vlc.player.load_tracks(tracks)


def cmd_search(items):
    fmt = lambda x: u'{:<12} {}'.format(x['id'], x)
    return '\n'.join(map(fmt, list(items)[:25])) + '\n'


def cmd_play(items):
    vlc.player.clear_playlist()
    vlc.player.load_tracks(items)


def cli_search(items):
    fmt = lambda x: u'{:<12} {}'.format(x['id'], x)
    sys.stdout.write('\n'.join(map(fmt, list(items)[:25])) + '\n')


def cli_play(items):
    # Entering player context starts VLC server
    with vlc.player:
        vlc.player.load_tracks(items)

        # Takes over control
        vlc.player.run()
    sys.stdout.write('\n\n')
