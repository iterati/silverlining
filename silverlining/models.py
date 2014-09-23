import collections
import functools
import os
import sqlite3

import soundcloud

from silverlining import (
    CLIENT_ID,
    client,
    utils,
)


def soundcloud_get(*args, **kwargs):
    results = client.get(*args, **kwargs)
    if isinstance(results, soundcloud.resource.Resource):
        return [results.obj]
    elif isinstance(results, soundcloud.resource.ResourceList):
        return list(map(lambda x: x.obj, results))


class UserNotFoundError(Exception):
    def __init__(self, username):
        super(UserNotFoundError, self).__init__(u'No user found for %s' % username)


class TrackNotFoundError(Exception):
    def __init__(self, query, user=None):
        msg = u'No tracks found named %s' % query
        if user:
            msg += u' for %s' % user['username']
        super(TrackNotFoundError, self).__init__(msg)


class PlaylistNotFoundError(Exception):
    def __init__(self, query, user=None):
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
        return list(map(Playlist, soundcloud_get('/users/%s/playlists' % self['id'])))


class Track(dict):
    def __init__(self, d):
        super(Track, self).__init__(d)
        if not 'username' in self:
            self['username'] = self['user']['username']

    @classmethod
    def get(cls, query=None, user=None):
        if query and utils.isint(query):
            return [cls(soundcloud_get('/tracks/%s' % query)[0])]

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
            return [cls(soundcloud_get('/playlists/%s' % query)[0])]

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
