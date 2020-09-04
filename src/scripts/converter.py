"""Usage:
  convert --all
  convert --stream <id> [<file>]

Options:
  --all     Get all filenames and styles from database. Without this argument
            converter will not change global style of subtitles.
  --stream  Same as --all, but converts only one stream.
"""

import os
import re
from datetime import timedelta
from multiprocessing import Pool

import tcd
from tcd.twitch import Message
from tcd.subtitles import SubtitlesASS
from docopt import docopt

from ..data.streams import streams, Segment, JoinedStream
from ..data.cache import cache
from ..data.config import tcd_config
from ..utils.ass import (EmptyLineError, SubtitlesReader,
                         SubtitlesWriter, SubtitlesEvent, SubtitlesStyle)


tcd.settings.update(tcd_config)

GROUPED_EMOTES = re.compile('([^\ ]+) x⁣([0-9]+)')


def unpack_emotes(line: str, pattern: re.Pattern = GROUPED_EMOTES) -> str:
    """Reverse changes made by tcd.twitch.Message.group()."""
    result = line

    for m in reversed(list(pattern.finditer(line))):
        mg = m.groups()
        ms = m.span()

        emote = mg[0].replace(' ', ' ')  # thin space to regular space
        count = int(mg[1])

        if count > 200:
            print(f'Ignoring line: {line}')
            continue

        result = ''.join((result[:ms[0]],
                          ' '.join([emote] * int(count)),
                          result[ms[1]:]))

        if len(result) > 500:
            print(f'{len(result)}/500 chars: {line}')
            return line

    return result


def unpack_line_breaks(line: str) -> str:
    """Reverse changes made by tcd.subtitles.SubtitleASS.wrap()."""
    return line.replace('\\N', '')


def convert_msg(msg: SubtitlesEvent) -> SubtitlesEvent:
    """Reapply all TCD settings for messages."""

    # Remove line breaks
    text = unpack_line_breaks(msg.text)

    # Repack emote groups
    text = unpack_emotes(text)
    text = Message.group(text, **tcd_config['group_repeating_emotes'])

    # Update message durations
    msg.duration = SubtitlesASS._duration(text)

    # Recreate line breaks
    text = SubtitlesASS.wrap(msg.username, text)

    msg.text = text
    return msg


def convert(ifn: str, ofn: str = None,
            style: SubtitlesStyle = None,
            func=lambda msg: msg):

    if ofn is None:
        ofn = f'{ifn}.tmp'
        replace = True
    else:
        replace = False

    r = SubtitlesReader(ifn)
    w = SubtitlesWriter(ofn, r.header, style if style else r.style,
                        tcd_config['ssa_events_format'][8:].split(', '))

    for event in r.events():
        try:
            event = func(event)

            if event is None:
                continue

            w.write(event)
        except EmptyLineError:
            continue

    if replace:
        os.rename(ofn, ifn)


def cut_subtitles(segment: Segment):
    if not os.path.exists(segment.stream.subtitles_path):
        raise FileNotFoundError(segment.stream.subtitles_path)

    def rebase_msg(msg):
        time = msg.start.time()
        time = 3600 * time.hour + 60 * time.minute + time.second

        # Drop all cut messages
        for cut in segment.cuts:
            if cut.value <= time <= cut.value + cut.duration:
                raise EmptyLineError()

        # Rebase messages after cuts
        delta = timedelta(seconds=sum([cut.duration
                                       for cut in segment.cuts
                                       if cut.value <= time]))
        msg.start -= delta
        msg.end -= delta

        return msg

    convert(segment.stream.subtitles_path,
            segment.subtitles_path,
            style=segment.stream.subtitles_style,
            func=rebase_msg)


def concatenate_subtitles(stream: JoinedStream):
    raise NotImplementedError


def generate_subtitles(segment):
    cache_key = f'generated-subtitles-{segment.hash}'
    cache_hash = segment.generated_subtitles_hash

    if cache_hash is None:
        if cache_key in cache:
            print(f'Removing generated subtitles of segment {segment.hash}')
            os.unlink(segment.generated_subtitles_path)
            cache.remove(cache_key)

        return

    if cache_key in cache and cache.get(cache_key) == cache_hash:
        return

    print(f'Generating subtitles for segment {segment.hash}')

    try:
        if isinstance(segment.stream, JoinedStream):
            concatenate_subtitles(segment.stream)
        elif len(segment.cuts) > 0:
            cut_subtitles(segment)
    except FileNotFoundError as ex:
        print(f'Skipping segment {segment.hash}: {ex.filename} does not exist')
        return
    except Exception as ex:
        print(f'Skipping segment {segment.hash}: {type(ex)}')
        return

    cache.set(cache_key, cache_hash)


def convert_file(file: str, style: SubtitlesStyle = None):
    print(f'Converting {file}')
    return convert(file, style=style, func=convert_msg)


def main(argv=None):
    args = docopt(__doc__, argv=argv)

    if args['--all']:
        tasks = [(s.subtitles_path, s.subtitles_style)
                 for s in streams.values()]
    elif args['--stream']:
        stream = streams[args['<id>']]
        if args['<file>']:
            tasks = [(args['<file>'], stream.subtitles_style)]
        else:
            tasks = [(stream.subtitles_path, stream.subtitles_style)]

    p = Pool(4)
    p.starmap(convert_file, tasks)
    p.close()


if __name__ == '__main__':
    main()
