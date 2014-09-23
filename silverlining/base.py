from silverlining import models


def parse_search_arguments(args):
    if not args or args[0] == '':
        return None, 'stream', None
    if args[0] in ['me', 'stream']:
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
    raise Exception("unable to parse command %s" % ' '.join(args))


def get_search_results(username, category, query):
    if category == 'stream':
        items = models.Track.get_from_stream(query)
    elif category == 'user':
        items = models.User.get(username)
    else:
        user = models.User.get_one(username) if username else None
        if category == 'track':
            items = models.Track.get(query, user)
        elif category == 'playlist':
            items = models.Playlist.get(query, user)

    return items


def get_search_interp(username, category, query):
    interp = ""
    if category == 'stream':
        interp += "your stream"
    elif username:
        interp += "%s's %ss" % (username, category)
    else:
        interp += "%ss" % category
    if query:
        interp += " for %s" % query
    return interp
