import requests

from silverlining import (
    CLIENT_ID,
    models,
    utils,
)
from silverlining.models import get_silverlining_playlist


def parse_search_arguments(args):
    if not args or args[0] == '':
        return None, 'sllist', None
    if args[0].startswith('http'):
        # it's a url
        resp = requests.get("https://api.soundcloud.com/resolve.json",
                            params={'url': args[0], 'client_id': CLIENT_ID})
        data = resp.json()
        return None, data['kind'], data['id']
    elif len(args) == 1 and utils.isint(args[0]):
        # it's an id, try it as a track and then as a playlist
        try:
            track = models.Track.get_one(args[0])
            return None, 'track', args[0]
        except models.TrackNotFoundError:
            pass
        try:
            playlist = models.Playlist.get_one(args[0])
            return None, 'playlist', args[0]
        except models.PlaylistNotFoundError:
            raise Exception("Unable to find item with id %s" % args[0])
    elif args[0] in ['me', 'stream']:
        if len(args) > 1:
            return None, 'stream', args[1]
        return None, 'stream', None
    elif args[0] in ['t', 'track', 'tracks']:
        if len(args) > 1:
            return None, 'track', args[1]
        raise Exception("not enough arguments")
    elif args[0] in ['p', 'playlist', 'playlists']:
        if len(args) > 1:
            return None, 'playlist', args[1]
        raise Exception("not enough arguments")
    else:
        if len(args) == 1:
            return args[0], 'user', None
        elif args[1] in ['t', 'track', 'tracks']:
            if len(args) > 2:
                return args[0], 'track', args[2]
            return args[0], 'track', None
        elif args[1] in ['p', 'playlist', 'playlists']:
            if len(args) > 2:
                return args[0], 'playlist', args[2]
            return args[0], 'playlist', None
        elif args[1] in ['s', 'stream']:
            if len(args) > 2:
                return args[0], 'stream', args[2]
            return args[0], 'stream', None
    raise Exception("unable to parse command %s" % ' '.join(args))


def get_search_results(username, category, query):
    if category == 'sllist':
        items = get_silverlining_playlist().tracks
        if query:
            items = utils.search_collection(items, query)
    elif category == 'stream':
        if username == 'me':
            items = models.Track.get_from_stream(query)
        else:
            user = models.User.get_one(username) if username else None
            items = user.stream
            if query:
                items = utils.search_collection(items, query)
    elif category == 'user':
        items = models.User.get(username)
    else:
        user = models.User.get_one(username) if username else None
        if category == 'track':
            items = models.Track.get(query, user)
        elif category == 'playlist':
            items = models.Playlist.get(query, user)

    return items


def get_search_interp(username, category, query, action='search'):
    interp = ""
    if category == 'sllist':
        interp += "silverlining playlist"
    elif category == 'stream':
        if username == 'me':
            interp += "your stream"
        else:
            interp = "%s's stream" % username
    elif username:
        if category == 'user':
            if action == 'search':
                interp += "users matching %s" % username
            else:
                interp += "%s's stream" % username
        else:
            interp += "%s's %ss" % (username, category)
    else:
        if query and utils.isint(query):
            interp += "%s id %s" % (category, query)
        else:
            interp += "%ss" % category
    if query and not utils.isint(query):
        interp += " for %s" % query
    return interp
