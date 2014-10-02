import collections
import functools
import signal
import sys
import termios
import tty

from fuzzywuzzy import process


class TimeoutError(Exception):
    pass


def isint(obj):
    try:
        int(obj)
    except (TypeError, ValueError):
        return False
    return True


def getch(timeout=0.1):
    """Returns single character of raw input or '' if nothing after timeout"""
    def _handle_timeout(signum, frame):
        raise TimeoutError()

    def _getch():
        try:
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return ch
        except TimeoutError:
            return ''

    signal.signal(signal.SIGALRM, _handle_timeout)
    signal.setitimer(signal.ITIMER_REAL, timeout)
    try:
        result = _getch()
    finally:
        signal.alarm(0)
    return result


def timestamp(time_pos, length):
    def sec_to_str(sec):
        sec = int(sec)
        hours, minutes, seconds = sec // 3600, (sec % 3600) // 60, sec % 60
        if sec > 3600:
            return "{:01}:{:02}:{:02}".format(hours, minutes, seconds)
        else:
            return "{:02}:{:02}".format(minutes, seconds)

    return "({}/{})".format(sec_to_str(time_pos), sec_to_str(length))


def search_collection(items, query, key='title'):
    """Levenstein fuzzy search"""
    d = {i[key]: i for i in items}
    bests = process.extractBests(query, list(d.keys()))
    if bests:
        return [d[match[0]] for match in bests]
    else:
        return []


class OrderedSet(collections.MutableSet):
    """http://code.activestate.com/recipes/576694/"""
    def __init__(self, iterable=None):
        self.end = end = []
        end += [None, end, end]         # sentinel node for doubly linked list
        self.map = {}                   # key --> [key, prev, next]
        if iterable is not None:
            self |= iterable

    def __len__(self):
        return len(self.map)

    def __contains__(self, key):
        return key in self.map

    def add(self, key):
        if key not in self.map:
            end = self.end
            curr = end[1]
            curr[2] = end[1] = self.map[key] = [key, curr, end]

    def discard(self, key):
        if key in self.map:
            key, prev, next = self.map.pop(key)
            prev[2] = next
            next[1] = prev

    def __iter__(self):
        end = self.end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[2]

    def __reversed__(self):
        end = self.end
        curr = end[1]
        while curr is not end:
            yield curr[0]
            curr = curr[1]

    def pop(self, last=True):
        if not self:
            raise KeyError('set is empty')
        key = self.end[1][0] if last else self.end[2][0]
        self.discard(key)
        return key

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self))

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return len(self) == len(other) and list(self) == list(other)
        return set(self) == set(other)
