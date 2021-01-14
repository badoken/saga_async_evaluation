from __future__ import annotations

from functools import reduce
from random import randint
from typing import Union


class Duration:
    def __init__(self, micros: int = 0, millis: int = 0, seconds: int = 0):
        self.micros: int = micros + (millis * 10 ** 3) + (seconds * 10 ** 6)

    @staticmethod
    def zero():
        return Duration()

    @staticmethod
    def rand_between(start: Duration, end: Duration) -> Duration:
        if start.is_negative:
            raise ValueError(f"Start should be >= 0, but was {start}")
        if start >= end:
            raise ValueError(f"Start should be < end, but start was {start} and end was {end}")

        return Duration(micros=randint(start.micros, end.micros))

    @staticmethod
    def avg(*durations: Duration) -> Duration:
        if not durations:
            return Duration.zero()
        return Duration.sum(*durations) / len(durations)

    @staticmethod
    def sum(*durations: Duration) -> Duration:
        if not durations:
            return Duration.zero()
        return reduce(lambda a, b: a + b, durations)

    def __add__(self, other: Duration) -> Duration:
        self._check_is_duration(other)
        return Duration(self.micros + other.micros)

    def __iadd__(self, other: Duration) -> Duration:
        self._check_is_duration(other)
        self.micros += other.micros
        return self

    def __sub__(self, other: Duration) -> Duration:
        self._check_is_duration(other)
        return Duration(self.micros - other.micros)

    def __radd__(self, other: Duration) -> Duration:
        self._check_is_duration(other)
        self.micros -= other.micros
        return self

    def __gt__(self, other: Duration) -> bool:
        self._check_is_duration(other)
        return self.micros > other.micros

    def __ge__(self, other: Duration) -> bool:
        self._check_is_duration(other)
        return self.micros >= other.micros

    def __lt__(self, other: Duration) -> bool:
        self._check_is_duration(other)
        return self.micros < other.micros

    def __le__(self, other: Duration) -> bool:
        self._check_is_duration(other)
        return self.micros <= other.micros

    def __mod__(self, other: Duration) -> Duration:
        self._check_is_duration(other)
        return Duration(micros=self.micros % other.micros)

    def __truediv__(self, other: Union[Duration, int, float]) -> Duration:
        divisor: Union[int, float]
        other_type = type(other)
        if other_type is Duration:
            divisor = other.micros
        elif other_type is int or other_type is float:
            divisor = other
        else:
            raise ValueError(f"Divisor should be either number or {type(Duration)} but it was {other}")
        return Duration(micros=int(self.micros / divisor))

    @property
    def is_positive(self) -> bool:
        return self.micros > 0

    @property
    def is_zero(self) -> bool:
        return self.micros == 0

    @property
    def is_negative(self) -> bool:
        return self.micros < 0

    @property
    def millis(self) -> float:
        return self.micros / 10 ** 3

    @property
    def seconds(self) -> float:
        return self.micros / 10 ** 6

    def __str__(self):
        return self.as_string

    def __repr__(self):
        return self.as_string

    def __eq__(self, other):
        if type(other) is not Duration:
            return False
        return self.micros == other.micros

    @property
    def as_string(self):
        string_value = "-" if self.is_negative else ""

        seconds = abs(self._hundreds(int(self.seconds)))
        if seconds != 0:
            string_value += f"{seconds}s"

        millis = abs(self._hundreds(int(self.millis)))
        if millis != 0:
            string_value += f"{millis}ms"

        micros = abs(self._hundreds(self.micros))
        if micros != 0:
            string_value += f"{micros}μs"

        if string_value == "":
            string_value = "zero"
        return f"🕒:{string_value}"

    @staticmethod
    def _hundreds(value: int):
        return value % (1000 if value > 0 else -1000)

    @staticmethod
    def _check_is_duration(argument):
        argument_type = type(argument)
        if argument_type is not Duration:
            raise TypeError(f"Expected to receive {type(Duration)} but was {argument_type}")
