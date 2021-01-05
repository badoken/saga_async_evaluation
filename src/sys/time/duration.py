from __future__ import annotations

from random import randint


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
    def _check_is_time_unit(argument):
        argument_type = type(argument)
        if argument_type is not Duration:
            TypeError("Expected to receive " + str(type(Duration)) + " but was " + str(argument_type))

    def __add__(self, other):
        self._check_is_time_unit(other)
        return Duration(self.nanos + other.nanos)

    def __iadd__(self, other):
        self._check_is_time_unit(other)
        self.nanos += other.nanos
        return self

    def __sub__(self, other):
        self._check_is_time_unit(other)
        return Duration(self.nanos - other.nanos)

    def __radd__(self, other):
        self._check_is_time_unit(other)
        self.nanos -= other.nanos
        return self

    def __gt__(self, other) -> bool:
        self._check_is_time_unit(other)
        return self.nanos > other.nanos

    def __ge__(self, other) -> bool:
        self._check_is_time_unit(other)
        return self.nanos >= other.nanos

    def __lt__(self, other) -> bool:
        self._check_is_time_unit(other)
        return self.nanos < other.nanos

    def __le__(self, other) -> bool:
        self._check_is_time_unit(other)
        return self.nanos <= other.nanos

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
