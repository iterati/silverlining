import requests
import soundcloud

from silverlining import (
    CLIENT_ID,
    client,
    utils,
)


def soundcloud_get(*args, **kwargs):
    try:
        results = client.get(*args, **kwargs)
    except requests.exceptions.HTTPError:
        return []

    if isinstance(results, soundcloud.resource.Resource):
        return [results.obj]
    elif isinstance(results, soundcloud.resource.ResourceList):
        return list(map(lambda x: x.obj, results))


class UserNotFoundError(Exception):
    def __init__(self, username):
        if utils.isint(query):
            msg = u"User with id %s not found" % username
        else:
            msg = u"No user found for %s" % username
        super(UserNotFoundError, self).__init__(msg)


class TrackNotFoundError(Exception):
    def __init__(self, query, user=None):
        if utils.isint(query):
            msg = u"Track with id %s not found" % query
        else:
            msg = u'No tracks found named %s' % query
            if user:
                msg += u' for %s' % user['username']
        super(TrackNotFoundError, self).__init__(msg)


class PlaylistNotFoundError(Exception):
    def __init__(self, query, user=None):
        if utils.isint(query):
            msg = u"Playlist with id %s not found" % query
        else:
            msg = u'No playlists found named %s' % query
            if user:
                msg += u' for %s' % user['username']
        super(PlaylistNotFoundError, self).__init__(msg)


class User(dict):
    @classmethod
    def get(cls, username=None):
        if utils.isint(username):
            users = soundcloud_get('/users/%s' % username)
        else:
            users = soundcloud_get('/users', q=username)
        return list(map(cls, users))

    @classmethod
    def get_one(cls, username=None):
        try:
            return cls.get(username)[0]
        except IndexError:
            raise UserNotFoundError(username)

    def __repr__(self):
        return u"%s" % self['username']

    @property
    def cli_display(self):
        return u'{:<12} {:24} {}'.format(self['id'], self['username'], self['full_name'])

    @property
    def tracks(self):
        return list(map(Track, soundcloud_get('/users/%s/tracks' % self['id'])))

    @property
    def playlists(self):
        return list(map(Playlist, soundcloud_get('/users/%s/playlists.json?limit=10' % self['id'])))

    @property
    def stream(self):
        url = "https://api-v2.soundcloud.com/profile/soundcloud:users:%s?limit=100"
        items = requests.get(url % self['id']).json()['collection']
        return list(
            map(Track,
                map(lambda x: x['track'],
                    filter(lambda x: x['type'] in ['track', 'track-repost'],
                           items))))


class Track(dict):
    def __init__(self, d):
        super(Track, self).__init__(d)
        if not 'username' in self:
            self['username'] = self['user']['username']

    @classmethod
    def get(cls, query=None, user=None):
        if query and utils.isint(query):
            tracks = soundcloud_get('/tracks/%s' % query)
            if not tracks:
                raise TrackNotFoundError(query)
            track = cls(tracks[0])
            tracks.extend(track.get_related())
            return [cls(track) for track in tracks]

        if user:
            tracks = user.tracks
            if query:
                tracks = utils.search_collection(tracks, query)
        else:
            tracks = soundcloud_get('/tracks', q=query)
        return list(map(cls, tracks))

    @classmethod
    def get_one(cls, query=None, user=None):
        try:
            return cls.get(query, user)[0]
        except IndexError:
            raise TrackNotFoundError(query, user)

    @classmethod
    def get_from_stream(cls, query=None):
        resp = soundcloud_get('/me/activities/tracks/affiliated')
        tracks = [cls(i['origin']) for i in resp[0]['collection']]
        if query:
            tracks = utils.search_collection(tracks, query)
        return tracks

    def get_related(self):
        resp = soundcloud_get('/tracks/%s/related' % self['id'])
        tracks = [Track(i) for i in resp]
        return tracks

    def __repr__(self):
        return u"%s - %s" % (self['username'], self['title'])

    @property
    def cli_display(self):
        return u"{:<12} {}".format(self['id'], self)

    @property
    def stream_uri(self):
        return self['stream_url'] + '?client_id=%s' % CLIENT_ID


class Playlist(dict):
    @classmethod
    def get(cls, query=None, user=None):
        if query and utils.isint(query):
            playlists = soundcloud_get('/playlists/%s' % query)
            if not playlists:
                raise PlaylistNotFoundError(query)
            return cls(playlists[0]).tracks

        if user:
            playlists = user.playlists
            if query:
                playlists = utils.search_collection(playlists, query)
        else:
            playlists = soundcloud_get('/playlists', q=query)
        return list(map(cls, playlists))

    @classmethod
    def get_one(cls, query=None, user=None):
        try:
            return cls.get(query, user)[0]
        except IndexError:
            raise PlaylistNotFoundError(query, user)

    def __init__(self, d):
        super(Playlist, self).__init__(d)

    def __repr__(self):
        return u"%s - %s" % (self['user']['username'], self['title'])

    @property
    def cli_display(self):
        return u"{:<12} {}".format(self['id'], self)

    @property
    def tracks(self):
        return list(map(Track, self['tracks']))


def get_silverlining_playlist():
    for playlist in client.get('me/playlists'):
        if playlist.title == 'Silverlining Playlist':
            playlist = Playlist(playlist.obj)
            break
    else:
        resp = client.post('/playlists', playlist={
            'title': 'Silverlining Playlist', 'sharing': 'private'})
        playlist = Playlist(resp.obj)

    return playlist
