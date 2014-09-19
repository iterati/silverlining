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
* `p` - previous track
* `.` - seek forward 15s
* `,` - seek backwards 15s
* `space` - pause/resume playback
* `l` - list local playlist tracks
* `s` - shuffle playlist
* `u` - display url
* `i` - display id
* `:` - enter command mode
* `q` - quit

## Command mode

While silverlining is playing, you can press `:` to enter command mode. While in
command mode you can enter full commands to be executed when you press return. For now,
the most useful feature is jump. :jump # or :j # to go to that index (shown next to tracks
when you hit `l`).
