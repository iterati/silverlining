import cmd
import readline
import shlex
import sys

from silverlining.base import (
    parse_search_arguments,
    get_search_results,
    get_search_interp,
)
from silverlining.models import Track


class CommandError(Exception):
    def __init__(self, message):
        self.message = message


class CommandMode(cmd.Cmd):
    prompt = '\n:'

    def __init__(self, player, *args, **kwargs):
        super(CommandMode, self).__init__(*args, **kwargs)
        self.player = player
        self._search_cache = []
        self.args = []

    def postcmd(self, stop, line):
        sys.stdout.write(u'{:120}\n'.format(self.player.now_playing))
        return stop

    def do_EOF(self, line):
        return True

    def parseline(self, line):
        args = super(CommandMode, self).parseline(line)[:-1]
        if args[1] == '':
            cmd, self.args = args[0], []
        else:
            cmd, self.args = args[0], args[1:]

        if cmd == 'q':
            cmd = 'quit'
        elif cmd == 'l':
            cmd = 'list'
        elif cmd == 'd':
            cmd = 'delete'
        elif cmd == 'j':
            cmd = 'jump'
        elif cmd == 'e':
            cmd = 'enqueue'
        elif cmd == 'h':
            cmd = 'history'

        return (cmd, args, line)

    def parse_range(self, r, allow_dot=True):
        if allow_dot:
            r.replace('.', str(self.player.current_track.idx))
        elif '.' in r:
            raise CommandError("self reference not supported for this command")

        rs = r.split(',')
        idxes = []
        for r in rs:
            if '-' in r:
                s, e = r.split('-')
                if s == '.':
                    if allow_dot:
                        s = self.player.current_track.idx
                    else:
                        raise CommandError("self reference not supported for this command")
                if e == '.':
                    if allow_dot:
                        e = self.player.current_track.idx
                    else:
                        raise CommandError("self reference not supported for this command")
                elif e == '*':
                    e = self.player.num_tracks
                idxes.extend(range(int(s), int(e) + 1))
            elif r == '.':
                if allow_dot:
                    idxes.append(self.player.current_track.idx)
                else:
                    raise CommandError("self reference not supported for this command")
            else:
                idxes.append(int(r))

        return sorted(list(set(idxes)))

    def do_quit(self, line):
        return True

    def do_list(self, line):
        fmt = lambda x: "{:<12} {}".format(x.idx, x)
        sys.stdout.write("Queue:\n")
        sys.stdout.write('\n'.join(map(fmt, self.player.queue)))

    def do_jump(self, line):
        if not self.args[0]:
            sys.stdout.write("jump requires a target, either an index or a search string\n")
            return

        track = self.player.get_track(self.args[0])
        if not track:
            sys.stdout.write("track not found\n")
            return

        self.player.jump(track)
        self.stdout.write("jumping to %s\n" % track)
        return

    def do_delete(self, line):
        if not self.args[0]:
            sys.stdout.write("delete takes a range argument\n")
            return

        try:
            indexes = self.parse_range(self.args[0])
        except CommandError:
            sys.stdout.write("invalid range\n")
            return

        tracks = []
        try:
            for i in indexes:
                tracks.append(self.player.queue[i])
        except IndexError:
            sys.stdout.write("invalid range\n")
        else:
            for track in tracks:
                self.player.remove_track(track)
            sys.stdout.write("deleted %s tracks\n" % len(tracks))
        return

    def do_search(self, line):
        try:
            username, category, query = parse_search_arguments(self.args)
        except Exception as e:
            sys.stdout.write("%s\n" % e)
        else:
            sys.stdout.write("Searching " + get_search_interp(username, category, query) + "\n")
            items = get_search_results(username, category, query)
            fmt = lambda x: "{:<12} {}".format(*x)
            sys.stdout.write(u"\n".join(map(fmt, items)) + "\n")
            self._search_cache = items
        return

    def do_enqueue(self, line):
        if not self.args[0]:
            sys.stdout.write("enqueue takes one argument\n")
            return

        try:
            indexes = self.parse_range(self.args[0])
        except CommandError:
            sys.stdout.write("invalid range\n")
            return

        tracks = []
        for i in indexes:
            try:
                item = self._search_cache[i]
                if item['kind'] == 'track':
                    tracks.append(item)
                else:
                    tracks.extend(item.tracks)
            except IndexError:
                sys.stdout.write('invalid range\n')
                return

        self.player.load_tracks(tracks)
        sys.stdout.write("Loaded %s tracks\n" % len(tracks))
        return

    def do_history(self, line):
        if len(self.args) == 0:
            sys.stdout.write('History:\n')
            for hist in self.player._history[::-1]:
                track = Track(hist)
                sys.stdout.write('{:<12} {}\n'.format(track))
        else:
            track = Track.get_one(self.player._history[-int(self.args[0])]['id'])
            self.player.load_tracks([track])
            sys.stdout.write('loaded %s\n' % track)
        return
