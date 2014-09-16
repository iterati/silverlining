import functools
import requests
import subprocess
import sys
import time

from silverlining import utils


HOTKEYS = {}


def hotkey(key, **kwargs):
    def decorator(func):
        HOTKEYS[key] = functools.partial(func, **kwargs)
        return func
    return decorator


class Player(object):
    _base_url = 'http://localhost:8080/requests/'
    _session = requests.session()
    _session.auth = requests.auth.HTTPBasicAuth('', 'silverlining')
    _playlist = {}
    _plid_lookup = {}
    _current_plid = None
    _time = 0
    _length = 0
    _running = False
    _proc = None

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

    def __exit__(self, *args):
        """Terminates the VLC process on exit"""
        self._proc.terminate()

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
        """Wrapper for  http requests to VLC API"""
        return self._session.get(self._base_url + endpoint, params=kwargs, verify=False)

    def _sync_playlist(self):
        """Syncs playlists with VLC"""
        resp = self.get('playlist.json').json()
        playlist = resp['children'][0]
        for i, d in enumerate(playlist['children']):
            track = self._playlist[d['uri']]
            track.position = i
            track.plid = int(d['id'])
            self._plid_lookup[track.plid] = track


    def _update_status(self):
        """updates current status"""
        resp = self.get('status.json').json()
        self._current_plid = resp['currentplid']
        self._time = resp['time']
        self._length = resp['length']

    @property
    def playlist(self):
        return sorted(self._playlist.values(), key=lambda x: x.position)

    @property
    def num_tracks(self):
        return len(self._playlist)

    @property
    def now_playing(self):
        return u"%s [%s/%s] %s" % (
            utils.timestamp(self._time, self._length),
            self.current_track.position + 1, self.num_tracks,
            self.current_track,
        )

    @property
    def current_track(self):
        return self._plid_lookup[self._current_plid]

    def get_track(self, target):
        try:
            if utils.isint(target):
                return player.playlist[int(target) - 1]
            else:
                return utils.search_collection(player.playlist, target)[0]
        except IndexError:
            return None

    def load_tracks(self, tracks):
        for track in list(tracks):
            self.get('status.json', command='in_enqueue', input=track.stream_uri,
                     name=track['title'])
            self._playlist[track.stream_uri] = track

        self._sync_playlist()

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

    @hotkey('p')
    def previous(self):
        self.get('status.json', command='pl_previous')
        return "Previous..."

    @hotkey('s')
    def shuffle(self):
        self.get('status.json', command='pl_sort', id=0, val="random")
        self._sync_playlist()
        return "Shuffling..."

    @hotkey('l')
    def list_playlist(self):
        fmt = lambda x: "{:<12} {}".format(x.position + 1, x)
        output = u'\r'
        output += u'\n'.join(map(fmt, self.playlist))
        output += u'\n'
        return output

    @hotkey('u')
    def display_url(self):
        return 'Soundcloud URL: %s' % self.current_track['permalink_url']

    @hotkey('i')
    def display_trackid(self):
        return 'Track id: %s' % self.current_track['id']

    @hotkey(':')
    def enter_command_mode(self):
        from silverlining.commands import parse_cmd_string
        cmd = input('\n:')
        cmd, args = parse_cmd_string(cmd)
        return cmd(*args)

    @hotkey('d')
    def remove_current_track(self):
        track = self.current_track
        self.next()
        self.remove_track(track)
        return "Removed %s" % track

    @hotkey('q')
    def quit(self):
        self._running = False
        return "Quitting..."

    def jump(self, track):
        self.get('status.json', command='pl_play', id=track.plid)

    def clear_playlist(self):
        self.get('status.json', commands='pl_empty')
        self._playlist = {}
        self._plid_lookup = {}

    def remove_track(self, track):
        self.get('status.json', command='pl_delete', id=track.plid)
        self._playlist.pop(track.stream_uri)
        self._plid_lookup.pop(track.plid)


player = Player()
