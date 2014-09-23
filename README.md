silverlining
============

## SoundCloud CLI Interface

Provides some access to the SoundCloud API and streaming playback from the
command line. You'll need to get an api key from here; http://soundcloud.com/you/apps
and add it to your environment variables.

## Installation

Install [VLC >= 2.1.0](http://www.videolan.org/vlc/download-macosx.html) in /Applications

Clone the repo:
`git clone https://github.com/iterati/silverlining.git`

Install the module:
`pip install --editable .`

Run it once to generate dotfiles (`~/.silverlining`):
`silverlining`

Enter your SoundCloud credentials in `~/.silverlining/config.json`

Play music:
`silverlining play feedme track patience`

## Usage grammar

There are two commands you can enter from the command line: search and play. Both can
be abbreviated to s and p respectively. They allow you to search users, tracks, and
playlists. Tracks and playlists are categories that can be searched and can also be
abbreviated to single letters. Up to the first 3 words after the command are parsed.

* First word is category? Words are category, username, search string
* Else? Words are username, category, search string

If the username or search string are integers, the resource is matched by id.

There are more commands that are available in command mode. See below for full list.

## Playback controls

* `n` - next track
* `.` - seek forward 15s
* `,` - seek backwards 15s
* `space` - pause/resume playback
* `l` - list local playlist tracks
* `s` - shuffle queue
* `u` - display url
* `i` - display id
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
