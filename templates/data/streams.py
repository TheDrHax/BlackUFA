#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from git import Repo
from requests import Session
from datetime import datetime
from subprocess import run, PIPE
from sortedcontainers import SortedList

from .cache import cached
from .config import config
from .timecodes import timecodes, Timecode, Timecodes, TimecodesSlice
from ..utils import _, load_json, last_line, count_lines, join, json_escape, indent


repo = Repo('.')
req = Session()


class Segment:
    def __init__(self, stream, **kwargs):
        self.references = SortedList(key=lambda x: Timecode(x.start))
        self.timecodes = None

        self.stream = stream
        self.twitch = stream.twitch

        def attr(key, default=None, func=lambda x: x):
            if key in kwargs:
                setattr(self, key, func(kwargs[key]))
            else:
                setattr(self, key, default)

        attr('segment', 0)

        for key in ['start', 'end', 'offset']:
            attr(key, func=lambda x: Timecode(x))

        for key in ['youtube', 'direct', 'torrent', 'official', 'note', 'name']:
            attr(key)

        self.fallback = False
        fallback = config['fallback']
        if not self.player_compatible and fallback['streams']:
            def check(url, code=200):
                return req.head(
                    url, allow_redirects=fallback['redirects']
                ).status_code == code

            url = f'{fallback["prefix"]}/{self.twitch}.mp4'

            if check(url):
                if self.offset:
                    self.start = self.offset
                    self.offset = None

                self.direct = url
                self.fallback = True

            torrent_url = f'{fallback["prefix"]}/{self.twitch}.torrent'

            if check(torrent_url):
                self.torrent = torrent_url
                self.fallback = True

        if len(stream.timecodes) > 0:
            self.timecodes = TimecodesSlice(stream.timecodes)

            if self.offset:
                self.timecodes.offset = self.offset

            if type(self) is Segment and self.start:
                self.timecodes.start = self.start

            end = None
            if self.end:
                end = self.end
            elif self.duration > 0:
                end = self.duration

            if end:
                if self.offset:
                    end += self.offset
                self.timecodes.end = end

    def reference(self):
        return SegmentReference(
            parent=self.references[0],
            name=' / '.join([r.game_name for r in self.references])
        )

    @property
    def player_compatible(self):
        return True in [getattr(self, key) is not None
                        for key in ['youtube', 'direct']]

    def attrs(self):
        attrs = []

        def escape_attr(attr):
            if type(attr) is str:
                return attr.replace('"', '&quot;')
            else:
                return str(attr)

        def add(key, func = lambda x: x):
            value = getattr(self, key)
            if value:
                value = func(value)
                value = escape_attr(value)
                attrs.append(f'data-{key}="{value}"')

        if self.segment != 0:
            add('segment')

        add('offset', lambda x: int(x))

        for key in ['start', 'end']:
            add(key, lambda x: int(x - Timecode(self.offset)))

        for key in ['name', 'twitch', 'youtube', 'direct']:
            add(key)

        if not self.player_compatible:
            attrs.append('style="display: none"')

        return ' '.join(attrs)

    @staticmethod
    @cached('duration-youtube-{0[0]}')
    def _duration_youtube(id):
        cmd = ['youtube-dl', '--get-duration', f'https://youtu.be/{id}']
        out = run(cmd, stdout=PIPE)

        if out.returncode == 0:
            t = out.stdout.decode('utf-8').strip()
            return Timecode(t).value
        else:
            raise Exception(f'`{" ".join(cmd)}` exited with '
                            f'non-zero code {out.returncode}')

    @property
    def duration(self):
        if self.youtube:
            return Timecode(self._duration_youtube(self.youtube))
        else:
            return Timecode(0)

    @property
    def date(self):
        return self.stream.date

    @property
    def hash(self):
        if self.segment == 0:
            return self.twitch
        else:
            return self.twitch + '.' + str(self.segment)

    @property
    def thumbnail(self):
        if self.youtube:
            return f'https://img.youtube.com/vi/{self.youtube}/mqdefault.jpg'
        else:
            return '/static/images/no-preview.png'

    def mpv_file(self):
        if self.youtube:
            return 'ytdl://' + self.youtube
        elif self.direct:
            return self.direct

    def mpv_args(self):
        base_url = 'https://blackufa.thedrhax.pw'
        res = f'--sub-file={base_url}/chats/v{self.twitch}.ass '
        offset = Timecode(0)
        if self.offset:
            offset = Timecode(self.offset)
            res += f'--sub-delay={-int(offset)} '
        if self.start:
            res += f'--start={int(Timecode(self.start) - offset)} '
        if self.end:
            res += f'--end={int(Timecode(self.end) - offset)} '
        return res.strip()

    @join()
    def to_json(self):
        keys = ['youtube', 'direct', 'offset', 'official', 'start', 'end']
        multiline_keys = ['note']

        multiline = True in [getattr(self, key) is not None
                             for key in multiline_keys]

        yield '{'
        yield '\n  ' if multiline else ' '

        first = True
        for key in keys:
            if getattr(self, key) is None:
                continue

            if key in ['direct', 'torrent', 'offset'] and self.fallback:
                continue

            if not first:
                yield ', '
            else:
                first = False

            yield f'"{key}": {json_escape(getattr(self, key))}'

        for key in multiline_keys:
            if getattr(self, key):
                if not first:
                    yield ',\n  '
                else:
                    first = False

                yield f'"{key}": {json_escape(getattr(self, key))}'

        yield '\n' if multiline else ' '
        yield '}'

    def __str__(self):
        return self.to_json()


class SegmentReference(Segment):
    def __init__(self, parent, game=None, **kwargs):
        self.parent = parent
        self.game = getattr(parent, 'game', game)

        if self.game is None:
            raise ValueError('`game` is required when referencing Segment')

        def attr(key, func=lambda x: x):
            if key in kwargs:
                setattr(self, key, func(kwargs[key]))

        for key in ['name', 'note']:
            attr(key)

        for key in ['start', 'end']:
            attr(key, lambda x: Timecode(x))

    @property
    def game_name(self):
        if self.game.type == 'list':
            return self.name
        else:
            return self.game.name

    def __getattr__(self, attr):
        return getattr(self.parent, attr)

    @join()
    def to_json(self):
        keys = ['name', 'twitch', 'segment', 'start', 'end']
        multiline_keys = ['note']

        def inherited(key):
            if key not in ['twitch', 'segment']:
                if getattr(self, key) == getattr(self.parent, key):
                    return True
            return False

        multiline = True in [getattr(self, key) and not inherited(key)
                             for key in multiline_keys]

        yield '{'
        yield '\n  ' if multiline else ' '

        first = True
        for key in keys:
            if getattr(self, key) is None or inherited(key):
                continue

            if key == 'segment':
                if len(self.parent.stream) > 1:
                    yield f', "segment": {self.parent.segment}'
                continue

            if not first:
                yield ', '
            else:
                first = False

            yield f'"{key}": {json_escape(getattr(self, key))}'

        for key in multiline_keys:
            if getattr(self, key) and not inherited(key):
                if not first:
                    yield ',\n  '
                else:
                    first = False

                yield f'"{key}": {json_escape(getattr(self, key))}'

        yield '\n' if multiline else ' '
        yield '}'

    def __str__(self):
        return self.to_json()


class Stream(list):
    def __init__(self, data, key):
        if type(data) is not list:
            raise TypeError(type(data))

        self.twitch = key
        self.games = []
        self.timecodes = Timecodes(timecodes.get(key) or {})

        for i, segment in enumerate(data):
            self.append(Segment(self, segment=i, **segment))

    @property
    @cached('duration-twitch-{0[0].twitch}')
    def _duration(self):
        line = last_line(_(f'chats/v{self.twitch}.ass'))
        if line is not None:
            return int(Timecode(line.split(' ')[2].split('.')[0]))

    @property
    def duration(self):
        return Timecode(self._duration)

    @property
    @cached('date-{0[0].twitch}')
    def _unix_time(self):
        args = ['--pretty=oneline', '--reverse', '-S', self.twitch]
        rev = repo.git.log(args).split(' ')[0]
        return repo.commit(rev).committed_date

    @property
    def date(self):
        return datetime.fromtimestamp(self._unix_time)

    @property
    @cached('messages-{0[0].twitch}')
    def _messages(self):
        lines = count_lines(_(f'chats/v{self.twitch}.ass'))
        return (lines - 10) if lines else None

    @property
    def messages(self):
        return self._messages or 0

    @join()
    def to_json(self):
        if len(self) > 1:
            yield '[\n'
            
            first = True
            for segment in self:
                if not first:
                    yield ',\n'
                else:
                    first = False

                yield indent(segment.to_json(), 2)
            
            yield '\n]'
        else:
            yield self[0].to_json()

    def __str__(self):
        return self.to_json()


class Streams(dict):
    def _from_dict(self, streams):
        for id, stream in streams.items():
            if type(stream) is dict:
                self[id] = Stream([stream], id)
            elif type(stream) is list:
                self[id] = Stream(stream, id)
            else:
                raise TypeError

    def _from_list(self, streams):
        for stream in streams:
            id = stream['twitch']
            self[id] = Stream([stream], id)

    @property
    def segments(self):
        for key, stream in self.items():
            for segment in stream:
                if len(segment.references) > 0:
                    yield segment

    def __init__(self, streams):
        if type(streams) is dict:
            self._from_dict(streams)
        elif type(streams) is list:
            self._from_list(streams)
        else:
            raise TypeError(type(streams))
    
    @join()
    def to_json(self):
        yield '{\n'
        
        first = True
        for key, stream in self.items():
            if not first:
                yield ',\n'
            else:
                first = False

            yield f'  "{key}": {indent(stream.to_json(), 2)[2:]}'

        yield '\n}'

    def __str__(self):
        return self.to_json()


streams = Streams(load_json('data/streams.json'))
