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
