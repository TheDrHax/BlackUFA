#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime


class Timecode(object):
    negative = False

    @staticmethod
    def text_to_sec(t):
        if len(t) == 0:
            return 0
        negative = (t[0] == '-')
        if negative:
            t = t[1:]
        s = sum(int(x) * 60 ** i
                for i, x in enumerate(reversed(t.split(":"))))
        return -s if negative else s

    @staticmethod
    def sec_to_text(s):
        result = []
        if s < 60:
            return '00:' + str(s).zfill(2)
        for i in [24*60*60, 60*60, 60, 1]:  # days, hours, minutes, seconds
            if len(result) > 0 or s // i > 0:
                result.append(str(s // i).zfill(2))
            s = s % i
        return ':'.join(result)

    def __init__(self, timecode, name=None):
        if (type(timecode) is str):
            value = self.text_to_sec(timecode)
        elif (type(timecode) is int):
            value = timecode
        elif (type(timecode) is Timecode):
            value = int(timecode)
        else:
            value = 0

        self.name = name
        self.value = abs(value)
        self.negative = value < 0

    def __str__(self):
        return ('-' if self.negative else '') + self.sec_to_text(self.value)

    def __repr__(self):
        return 'Timecode({}, {})'.format(str(self), self.name)

    def __int__(self):
        return (-1 if self.negative else 1) * self.value

    @staticmethod
    def _type_check(arg):
        if type(arg) not in [Timecode, Timecodes, int]:
            raise TypeError(type(arg))

    def __add__(self, other):
        self._type_check(other)
        return Timecode(int(self) + int(other), self.name)

    def __sub__(self, other):
        self._type_check(other)
        return Timecode(int(self) - int(other), self.name)

    def __ge__(self, other):
        self._type_check(other)
        return int(self) >= int(other)

    def __gt__(self, other):
        self._type_check(other)
        return int(self) > int(other)

    def __le__(self, other):
        self._type_check(other)
        return int(self) <= int(other)

    def __lt__(self, other):
        self._type_check(other)
        return int(self) < int(other)


class Timecodes(list):
    offset = Timecode(0)

    def __init__(self, timecodes={}, name=None):
        if type(timecodes) is not dict:
            raise TypeError(type(timecodes))

        self.name = name
        for key, value in timecodes.items():
            try:
                self.append(Timecode(key, value))
            except ValueError:
                self.append(Timecodes(value, key))

    def __int__(self):
        return int(self[0]) if len(self) > 0 else 0

    def values(self):
        return sorted(self)

    def append(self, value):
        if type(value) not in [Timecode, Timecodes]:
            raise TypeError(type(value))
        for i, item in enumerate(self):
            if item >= value:
                return self.insert(i, value)
        super(Timecodes, self).append(value)
        self.value = int(self[0])

    def start_at(self, offset):
        self.offset += offset

        for value in self.copy():
            if type(value) is Timecode and offset > value:
                self.remove(value)
            elif type(value) is Timecodes:
                value.start_at(offset)
                if len(value) == 0:
                    self.remove(value)

        for i, t in enumerate(self.copy()):
            if type(t) is Timecode:
                self[i] = t - offset

    def end_at(self, offset):
        for value in self.copy():
            if offset - self.offset <= value:
                self.remove(value)


class TimecodeHelper:
    delay = 15  # Delay of `streamlink --stream-url` + `mpv` (quality='best')

    @staticmethod
    def time():
        """Get current time as Timecode."""
        return Timecode(str(datetime.time(datetime.now())).split('.')[0])

    def __init__(self, start):
        self.start = Timecode(start)

    def get(self):
        return self.time() - self.start - Timecode(self.delay)
