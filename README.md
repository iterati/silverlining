silverlining
============

# A SoundCloud CLI Interface for Mac OS X

## Installation

Get application client id and api key from [SoundCloud](http://soundcloud.com/you/apps)

Install [VLC >= 2.1.0](http://www.videolan.org/vlc/download-macosx.html) in /Applications

Clone the repo:

`git clone https://github.com/iterati/silverlining.git`

Install the module:

`pip install --editable .`

Run it once to generate dotfiles (`~/.silverlining`):

`silverlining`

Enter your SoundCloud credentials and api key in `~/.silverlining/config.json`

To allow the `u` (show url) command to copy the url to your clipboard, you will
need to have brew installed and run:

`brew install reattach-to-user-namespace --wrap-pbcopy-and-pbpaste`

```
{
  "username": your_soundcloud_username,
  "password": your_soundcloud_password,
  "client_id": your_soundcloud_app_client_id,
  "secret_key": your_soundcloud_app_secret_key
}
```

Play music:

`silverlining play feedme track patience`

## Usage grammar

There are two commands you can enter from the command line: search and play. Both can
be abbreviated to s and p respectively. They allow you to search users, tracks, and
playlists. Tracks and playlists are categories that can be searched and can also be
abbreviated to single letters. Up to the first 3 words after the command are parsed.

* No first word? Show or play your silverlining playlist.
* First word is category? Words are category and search string
* Else? Words are username, category, and search string

If the username or search string are integers, the resource is matched by id.

There are more commands that are available in command mode. See below for full list.

### Categories

There are three categories that can be used:

* Stream - Your activity stream or the tracks posted and reposted by another user
* Tracks - Tracks posted by a user
* Playlists - Playlists posted by a user

### Examples

`silverlining`
Lists your silverlining playlist

`silverlining stream`
Lists your SoundCloud stream

`silverlining s feedme`
Search for users matching 'feedme'

`silverlining s feedme stream`
List tracks (posted and reposted) from first user matching 'feedme'

`silverlining s 12345 t`
List tracks for user with id 12345

`silverlining s feedme p`
List playlists from first user matching 'feedme'

`silverlining s feedme t patience`
Search for 'patience' in tracks from first user matching 'feedme'

`silverlining s t patience`
Search tracks for 'patience'

`silverlining p`
Plays your silverlining playlist

`silverlining p stream`
Plays your SoundCloud stream

`silverlining p feedme`
Plays stream (posted and reposted) from first user matching 'feedme'

`silverlining p feedme t`
Plays tracks from first user matching 'feedme'

`silverlining p feedme p`
Plays first playlist from first user matching 'feedme'

`silverlining p https://soundcloud.com/feedme/patience`
Plays the item at the URL (user's stream, track + related, or playlist's tracks)

## Playlist

Silverlining creates a private playlist titled "Silverlining Playlist" on your
SoundCloud account when first ran. You can list this playlist by running
`silverlining s` without any other arguments and play it with `silverlining p`.

The only current way to edit the playlist is through the SoundCloud web ui.

## Playback controls

* `n` - next track
* `.` - seek forward 15s
* `,` - seek backwards 15s
* `space` - pause/resume playback
* `l` - list queue
* `s` - shuffle queue
* `u` - display url
* `i` - display id
* `p` - adds current track to your silverlining playist
* `:` - enter command mode
* `q` - quit
* `X` - clears your queue

## Command mode

Command mode is an interactive way to list, delete, move around, search, or add
to your playlist. The 6 commands in command mode are:

* `q` - quits command mode
* `l` - lists your queue  as `idx    track` with idx being the track's index in
    the queue
* `j` - jumps to a track in your playlist. If argument is a string, jump goes to
    closest fuzzy string match
* `d` - deletes items from your queue
* `s` - searches SoundCloud with the same grammar as from the command line. Tracks
    are listed `idx    track` instead of `sc_id   track`
* `e` - enqueues tracks from search
* `h` - h by itself lists your history, h + # will load the track at idx

### Range syntax

Both the delete and enqueue commands accept ranges. Examples:

* `0` - refers to idx 0
* `0,3` - refers to idxes 0 and 3
* `0-3` - refers to idxes 0, 1, 2, and 3
* `0,3-5` - refers to idxes 0, 3, 4, and 5

The delete command also accepts `.` as a reference to the current track's idx:

* `.` - refers to the current track's idx
* `.-3` - refers to current track's idx (assume it's 1), 2, and 3

When using enqueue, idxes refer to the most recently performed search results.
Results are cached and can be referred to multiple times without needing to search
again.
