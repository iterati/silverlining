import functools
import shlex
import sys

from silverlining import (
    parse_cli_arguments,
    get_items,
    get_interp,
    models,
    utils,
    vlc,
)


COMMANDS = {}


class CommandError(Exception):
    def __init__(self, message):
        self.message = message


def command(*abbrs):
    def decorator(func):
        COMMANDS[func.__name__] = func
        for abbr in abbrs:
            COMMANDS[abbr] = func
        return func
    return decorator


def parse_cmd(cmd_in):
    args = shlex.split(cmd_in)
    cmd, args = args[0], args[1:]
    if cmd not in COMMANDS:
        raise CommandError("Command not recognized.")
    return COMMANDS[cmd], args


def parse_range(range, allow_dot=True):
    ranges = range.split(',')
    idxes = []
    for r in ranges:
        if '-' in r:
            s, e = r.split('-')
            if s == '.':
                if allow_dot:
                    s = vlc.player.current_track.idx
                else:
                    raise CommandError("self reference not supported for this command")
            if e == '.':
                if allow_dot:
                    e = vlc.player.current_track.idx
                else:
                    raise CommandError("self reference not supported for this command")
            idxes.extend(range(int(s), int(e) + 1))
        elif r == '.':
            if allow_dot:
                idxes.append(vlc.player.current_track.idx)
            else:
                raise CommandError("self reference not supported for this command")
        else:
            idxes.append(int(r))

    return idxes


@command('q')
def quit(args):
    vlc.player._cmd_mode = False
    return "Exit command mode", None


@command('l', 'list')
def list_playlist(args):
    items = vlc.player.playlist
    fmt = lambda x: "{:<12} {}".format(*x)
    output = "Listing playlist:\n"
    output += '\n'.join(map(fmt, enumerate(items)))
    return output, None


@command('j')
def jump(args):
    target = args[0]
    track = vlc.player.get_track(target)
    if not track:
        return "Track not found", None

    vlc.player.jump(track)
    return "Jumping to %s" % track, None


@command('s')
def search(args):
    username, category, query = parse_cli_arguments(args)
    items = get_items(username, category, query)
    fmt = lambda x: "{:<12} {}".format(*x)
    output = "Searching " + get_interp(username, category, query) + ":\n"
    output += "\n".join(map(fmt, enumerate(items)))
    return output, items


@command('e')
def enqueue(args):
    if len(args) == 0:
        raise CommandError("Enqueue takes one argument")

    try:
        idxes = parse_range(args[0], allow_dot=False)
    except:
        raise CommandError("Unable to parse range")

    tracks = []
    for i in idxes:
        if i > len(vlc.player._cmd_cache):
            raise CommandError("Range index out of range.")
        item = vlc.player._cmd_cache[idx]
        if item['kind'] == 'track':
            tracks.append(item)
        else:
            tracks.extend(item.tracks)

    vlc.player.load_tracks(tracks)
    return "Loaded %s tracks" % len(tracks), None


@command('d')
def delete(args):
    if len(args) == 0:
        raise CommandError("Delete takes one argument")

    try:
        ranges = parse_range(args[0])
    except:
        raise CommandError("Unable to parse range")

    tracks = []
    try:
        for r in ranges:
            if isinstance(r, tuple):
                for i in range(*r):
                    tracks.append(vlc.player.get_track(i))
            else:
                tracks.append(vlc.player.get_track(r))
        for track in tracks:
            vlc.player.remove_track(track)
    except:
        raise CommandError("Unable to perform command.")
    return "Deleted %s tracks" % len(tracks), None
