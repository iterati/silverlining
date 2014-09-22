import functools
import requests
import subprocess
import sys
import time

from silverlining import utils


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
    _current_id = None
    _time = 0
    _length = 0
    _running = False
    _cmd_mode = False
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
        """Wrapper for http requests to VLC API"""
        return self._session.get(self._base_url + endpoint, params=kwargs, verify=False)

    def load_tracks(self, tracks):
        for track in list(tracks):
            self.get('status.json', command='in_enqueue', input=track.stream_uri,
                     name=track['id'])
            self._tracks[int(track['id'])] = track

        self._sync_playlist()

    def remove_track(self, track):
        self.get('status.json', command='pl_delete', id=track.plid)
        track = self._tracks[track['id']]
        if track == self.current_track:
            self.next()
            self._tracks.pop(track['id'])
            self.play()
        else:
            self._tracks.pop(track['id'])
        for idx in range(track.idx, len(self.playlist)):
            self.playlist[idx].idx -= 1

    def _sync_playlist(self):
        """Syncs playlists with VLC"""
        resp = self.get('playlist.json').json()
        playlist = resp['children'][0]
        for i, d in enumerate(playlist['children']):
            track = self._tracks[int(d['name'])]
            track.idx = i
            track.plid = int(d['id'])

    def _update_status(self):
        """updates current status"""
        resp = self.get('status.json').json()
        try:
            self._current_id = int(resp['information']['category']['meta']['title'])
        except KeyError:
            self._current_id = None
        self._time = resp['time']
        self._length = resp['length']

    @property
    def playlist(self):
        return sorted(self._tracks.values(), key=lambda x: getattr(x, 'idx'))

    @property
    def num_tracks(self):
        return len(self._tracks)

    @property
    def current_track(self):
        if self._current_id and self._current_id in self._tracks:
            return self._tracks[self._current_id]
        else:
            return None

    @property
    def now_playing(self):
        if self.current_track:
            idx = getattr(self.current_track, 'idx', 0)
            return u"%s [%s/%s] %s" % (
                utils.timestamp(self._time, self._length),
                idx + 1, self.num_tracks, self.current_track,
            )
        else:
            return "Stopped"

    def get_track(self, target):
        try:
            if utils.isint(target):
                return player.playlist[int(target)]
            else:
                return utils.search_collection(player.playlist, target)[0]
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

    @hotkey('p')
    def previous(self):
        self.get('status.json', command='pl_previous')
        return "Previous..."

    @hotkey('s')
    def shuffle(self):
        self.get('status.json', command='pl_sort', id=0, val="random")
        self._sync_playlist()
        return "Shuffling..."

    def _list_playlist(self):
        fmt = lambda x: "{:<12} {}".format(getattr(x, 'idx', 0), x)
        return u'\n'.join(map(fmt, self.playlist))

    def jump(self, track):
        self.get('status.json', command='pl_play', id=track.plid)

    def _get_result(self, index):
        try:
            return self._cmd_cache[int(index)]
        except:
            return None

    # @hotkey('l')
    def list_playlist(self):
        fmt = lambda x: "{:<12} {}".format(getattr(x, 'idx', 0), x)
        output = u'\r'
        output += self._list_playlist()
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

    @hotkey('d')
    def remove_current_track(self):
        track = self.current_track
        self.remove_track(track)
        self.play()
        return "Removed %s" % track

    @hotkey('q')
    def quit(self):
        self._running = False
        return "Quitting..."

    def clear_playlist(self):
        self.stop()
        self.get('status.json', command='pl_empty')
        self._update_status()
        return "Cleared playlist"

    @hotkey(':')
    def enter_command_mode(self):
        from silverlining.commands import parse_cmd, CommandError
        self._cmd_mode = True
        self._cmd_cache = []
        while self._cmd_mode:
            cmd = input('\n:')
            output = None
            try:
                cmd, args = parse_cmd(cmd)
            except CommandError as e:
                output = e.message
            else:
                try:
                    output, cache = cmd(args)
                except CommandError as e:
                    output = e.message
                else:
                    if cache:
                        self._cmd_cache = cache
            if output:
                sys.stdout.write(u'\r{:120}'.format(output))
        return ""


player = Player()
