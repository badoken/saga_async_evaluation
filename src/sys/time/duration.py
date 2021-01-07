from __future__ import annotations

from functools import reduce
from numbers import Number
from random import randint
from typing import Union, Iterable, TypeVar, Collection


class Duration:
    def __init__(self, nanos: int = 0, micros: int = 0, millis: int = 0, seconds: int = 0):
        self.nanos: int = nanos + (micros * 10 ** 3) + (millis * 10 ** 6) + (seconds * 10 ** 9)

    @staticmethod
    def zero():
        return Duration()

    @staticmethod
    def rand_between(start: Duration, end: Duration) -> Duration:
        if start.is_negative:
            raise ValueError("Start should be >= 0, but was " + str(start))
        if start >= end:
            raise ValueError("Start should be < end, but start was " + str(start) + " and end was " + str(end))

        return Duration(nanos=randint(start.nanos, end.nanos))

    @staticmethod
    def avg(durations: Collection[Duration]) -> Duration:
        if not durations:
            return Duration.zero()
        return Duration.sum(durations) / len(durations)

    @staticmethod
    def sum(durations: Collection[Duration]) -> Duration:
        if not durations:
            return Duration.zero()
        return reduce(lambda a, b: a + b, durations)

    @staticmethod
    def _check_is_duration(argument):
        argument_type = type(argument)
        if argument_type is not Duration:
            raise TypeError("Expected to receive " + str(type(Duration)) + " but was " + str(argument_type))

    def __add__(self, other: Duration) -> Duration:
        self._check_is_duration(other)
        return Duration(self.nanos + other.nanos)

    def __iadd__(self, other: Duration) -> Duration:
        self._check_is_duration(other)
        self.nanos += other.nanos
        return self

    def __sub__(self, other: Duration) -> Duration:
        self._check_is_duration(other)
        return Duration(self.nanos - other.nanos)

    def __radd__(self, other: Duration) -> Duration:
        self._check_is_duration(other)
        self.nanos -= other.nanos
        return self

    def __gt__(self, other: Duration) -> bool:
        self._check_is_duration(other)
        return self.nanos > other.nanos

    def __ge__(self, other: Duration) -> bool:
        self._check_is_duration(other)
        return self.nanos >= other.nanos

    def __lt__(self, other: Duration) -> bool:
        self._check_is_duration(other)
        return self.nanos < other.nanos

    def __le__(self, other: Duration) -> bool:
        self._check_is_duration(other)
        return self.nanos <= other.nanos

    def __mod__(self, other: Duration) -> Duration:
        self._check_is_duration(other)
        return Duration(nanos=self.nanos % other.nanos)

    def __truediv__(self, other: Union[Duration, int, float]) -> Duration:
        divisor: Union[int, float]
        other_type = type(other)
        if other_type is Duration:
            divisor = other.nanos
        elif other_type is int or other_type is float:
            divisor = other
        else:
            raise ValueError("Divisor should be either number or Duration but it was " + str(other))
        return Duration(nanos=int(self.nanos / divisor))

    @property
    def is_positive(self) -> bool:
        return self.nanos > 0

    @property
    def is_zero(self) -> bool:
        return self.nanos == 0

    @property
    def is_negative(self) -> bool:
        return self.nanos < 0

    @property
    def micros(self) -> float:
        return self.nanos / 10 ** 3

    @property
    def millis(self) -> float:
        return self.nanos / 10 ** 6

    @property
    def seconds(self) -> float:
        return self.nanos / 10 ** 9

    def __str__(self):
        return self.as_string

    def __repr__(self):
        return self.as_string

    def __eq__(self, other):
        if type(other) is not Duration:
            return False
        return self.nanos == other.nanos

    @property
    def as_string(self):
        string_value = "-" if self.is_negative else ""

        seconds = abs(self._hundreds(int(self.seconds)))
        if seconds != 0:
            string_value += str(seconds) + "s"

        millis = abs(self._hundreds(int(self.millis)))
        if millis != 0:
            string_value += str(millis) + "ms"

        micros = abs(self._hundreds(int(self.micros)))
        if micros != 0:
            string_value += str(micros) + "μs"

        nanos = abs(self._hundreds(self.nanos))
        if nanos != 0:
            string_value += str(nanos) + "ns"

        if string_value == "":
            string_value = "zero"
        return "🕒:" + string_value + ""

    @staticmethod
    def _hundreds(value: int):
        return value % (1000 if value > 0 else -1000)
