import functools
import simplejson
import subprocess
import sys
import time

import requests

from silverlining import (
    HIST_FILE,
    utils,
)
from silverlining.command import CommandMode


HOTKEYS = {}


def hotkey(keys, **kwargs):
    def decorator(func):
        for key in keys:
            HOTKEYS[key] = functools.partial(func, **kwargs)
        return func
    return decorator


class Player(object):
    _base_url = 'http://localhost:8080/requests/'
    _session = requests.session()
    _session.auth = requests.auth.HTTPBasicAuth('', 'silverlining')
    _tracks = {}
    current_track = None
    _time = 0
    _length = 0
    _running = False
    _cmd_mode = False
    _proc = None
    _history = []

    def __enter__(self):
        """Starts the VLC server and waits for it to start up before returning"""
        if self._proc:
            raise Exception("There's already a VLC process")

        self._proc = subprocess.Popen([
            "/Applications/VLC.app/Contents/MacOS/VLC",
            "--quiet", "--intf", "http", "--http-password", "silverlining",
        ], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)

        while True:
            try:
                self.get('status.json')
                return self
            except requests.exceptions.ConnectionError:
                pass

        try:
            with open(HIST_FILE, 'rb') as f:
                self._history = simplejson.loads(f.read())
                self._history.reverse()
        except IOError:
            pass

    def __exit__(self, *args):
        """Terminates the VLC process on exit"""
        self._proc.terminate()
        self._history.reverse()
        with open(HIST_FILE, 'w') as f:
            data = simplejson.dumps(self._history[:50], indent=2)
            f.write(data + '\n')

    def _write_track_to_history(self, track):
        self._history.append({
            'id': track['id'],
            'title': track['title'],
            'permalink_url': track['permalink_url'],
            'stream_url': track['stream_url'],
            'username': track['username'],
        })

    def run(self):
        """Runs the poor man's thread"""
        self._running = True
        self.play()
        while self._running:
            self._update_status()
            keypress = utils.getch(1)
            if keypress in HOTKEYS:
                output = HOTKEYS[keypress](self)
                if output:
                    sys.stdout.write(u'\r{:120}\n'.format(output))

            sys.stdout.write(u'\r{:120}'.format(self.now_playing))

    def get(self, endpoint, **kwargs):
        """Wrapper for http requests to VLC API"""
        return self._session.get(self._base_url + endpoint, params=kwargs, verify=False)

    def load_tracks(self, tracks):
        for track in list(tracks):
            self.get('status.json', command='in_enqueue', input=track.stream_uri,
                     name=track['id'])
            self._tracks[int(track['id'])] = track

        self._sync_queue()

    def remove_track(self, track):
        self.get('status.json', command='pl_delete', id=track.plid)
        try:
            track = self._tracks[track['id']]
        except KeyError:
            return
        if track == self.current_track:
            self.next()
            self._tracks.pop(track['id'])
            self.play()
        else:
            self._tracks.pop(track['id'])
        for idx in range(track.idx, len(self.queue)):
            self.queue[idx].idx -= 1

    def _sync_queue(self):
        """Syncs queue with VLC"""
        resp = self.get('playlist.json').json()
        playlist = resp['children'][0]
        for i, d in enumerate(playlist['children']):
            track = self._tracks[int(d['name'])]
            track.idx = i
            track.plid = int(d['id'])

    def _update_track(self, vlc_id):
        if vlc_id is None and self.current_track is not None:
            #track became none
            current_track = self.current_track
            self.current_track = None
            #delete current_track
            self._write_track_to_history(current_track)
            self.remove_track(current_track)

        if vlc_id is not None and self.current_track and vlc_id != self.current_track['id']:
            #track changed
            current_track = self.current_track
            self.current_track = self._tracks[vlc_id]
            #delete current track
            self._write_track_to_history(current_track)
            self.remove_track(current_track)

        if self.current_track is None and vlc_id is not None:
            self.current_track = self._tracks[vlc_id]

    def _update_status(self):
        """updates current status"""
        resp = self.get('status.json').json()
        try:
            vlc_id = int(resp['information']['category']['meta']['title'])
        except KeyError:
            vlc_id = None
        self._update_track(vlc_id)
        if self.current_track is None and self.num_tracks > 0:
            self.play()
        self._length = resp['length']
        self._time = resp['time']

    @property
    def queue(self):
        return sorted(self._tracks.values(), key=lambda x: getattr(x, 'idx'))

    @property
    def num_tracks(self):
        return len(self._tracks)

    @property
    def now_playing(self):
        if self.current_track:
            return u"[%s] %s %s" % (
                self.num_tracks,
                utils.timestamp(self._time, self._length),
                self.current_track,
            )
        else:
            return "Stopped"

    def get_track(self, target):
        try:
            if utils.isint(target):
                return self.queue[int(target)]
            else:
                return utils.search_collection(self.queue, target)[0]
        except IndexError:
            return None

    # VLC Controls
    def play(self):
        self.get('status.json', command='pl_play')

    def stop(self):
        self.get('status.json', command='pl_stop')

    @hotkey('.', val='+15')
    @hotkey(',', val='-15')
    def seek(self, val):
        self.get('status.json', command='seek', val=val)

    @hotkey(' ')
    def pause(self):
        self.get('status.json', command='pl_pause')

    @hotkey('n')
    def next(self):
        self.get('status.json', command='pl_next')
        return "Next..."

    @hotkey('s')
    def shuffle(self):
        self.get('status.json', command='pl_sort', id=0, val="random")
        self._sync_queue()
        return "Shuffling..."

    def _list_queue(self):
        fmt = lambda x: "{:<12} {}".format(getattr(x, 'idx', 0), x)
        return u'\n'.join(map(fmt, self.queue))

    def jump(self, track):
        self.get('status.json', command='pl_play', id=track.plid)
        tracks = self.queue[:track.idx]
        for track in tracks:
            self.remove_track(track)

    @hotkey('l')
    def list_queue(self):
        fmt = lambda x: "{:<12} {}".format(getattr(x, 'idx', 0), x)
        output = u'\r'
        output += self._list_queue()
        output += u'\n'
        return output

    @hotkey('u')
    def display_url(self):
        if self.current_track:
            return 'Soundcloud URL: %s' % self.current_track['permalink_url']
        else:
            return 'Not playing'

    @hotkey('i')
    def display_trackid(self):
        if self.current_track:
            return 'Track id: %s' % self.current_track['id']
        else:
            return 'Not playing'

    @hotkey('q')
    def quit(self):
        self._running = False
        return "Quitting..."

    @hotkey('X')
    def clear_queue(self):
        self.stop()
        self.get('status.json', command='pl_empty')
        self._update_status()
        return "Cleared queue"

    @hotkey(':')
    def enter_command_mode(self):
        CommandMode(self).cmdloop()
