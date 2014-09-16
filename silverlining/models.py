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
    kwargs['limit'] = 100
    results = client.get(*args, **kwargs)
    if isinstance(results, soundcloud.resource.Resource):
        return [results.obj]
    elif isinstance(results, soundcloud.resource.ResourceList):
        return list(map(lambda x: x.obj, results))


class UserNotFoundError(Exception):
    def __init__(self, username):
        super(UserNotFoundError, self).__init__(u'No user found for %s' % username)


class TrackNotFoundError(Exception):
    def __init__(self, title, user=None):
        msg = u'No tracks found named %s' % title
        if user:
            msg += ' for %s' % user['username']
        super(TrackNotFoundError, self).__init__(msg)


class PlaylistNotFoundError(Exception):
    def __init__(self, title, user=None):
        msg = u'No playlists found named %s' % title
        if user:
            msg += ' for %s' % user['username']
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

    def __init__(self, d):
        super(User, self).__init__(d)

    def __repr__(self):
        return self['username']

    @property
    def tracks(self):
        return list(map(Track, soundcloud_get('/users/%s/tracks' % self['id'])))

    @property
    def playlists(self):
        return list(map(Playlist, soundcloud_get('/users/%s/playlists' % self['id'])))


class Track(dict):
    @classmethod
    def get(cls, title=None, user=None):
        if not (title or user):
            raise TypeError("Need title and/or user")

        if title and utils.isint(title):
            tracks = soundcloud_get('/tracks/%s' % title)
            title = tracks[0]['title']

        if user:
            tracks = user.tracks
            if title:
                tracks = utils.search_collection(tracks, title)
        else:
            tracks = soundcloud_get('/tracks', q=title)
        return list(map(cls, tracks))

    @classmethod
    def get_one(cls, title=None, user=None):
        try:
            return cls.get(title, user)[0]
        except IndexError:
            raise TrackNotFoundError(title, user)

    def __init__(self, d):
        position = None
        plid = None
        super(Track, self).__init__(d)

    def __repr__(self):
        return self['title']

    @property
    def stream_uri(self):
        return self['stream_url'] + '?client_id=%s' % CLIENT_ID


class Playlist(dict):
    @classmethod
    def get(cls, title=None, user=None):
        if not (title or user):
            raise TypeError("Need title and/or user")

        if title and utils.isint(title):
            return [cls(soundcloud_get('/playlists/%s' % title)[0])]

        if user:
            playlists = user.playlists
            if title:
                playlists = utils.search_collection(playlists, title)
        else:
            playlists = soundcloud_get('/playlists', q=title)
        return list(map(cls, playlists))

    @classmethod
    def get_one(cls, title=None, user=None):
        try:
            return cls.get(title, user)[0]
        except IndexError:
            raise PlaylistNotFoundError(title, user)

    def __init__(self, d):
        super(Playlist, self).__init__(d)

    def __repr__(self):
        return self['title']

    @property
    def tracks(self):
        return list(map(Track, self['tracks']))
