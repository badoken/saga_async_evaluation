from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID, uuid5, uuid4


class Duration:
    def __init__(self, micros: int = 0, millis: int = 0, seconds: int = 0):
        self.micros: int = micros + (millis * 10 ** 3) + (seconds * 10 ** 6)

    @staticmethod
    def zero():
        return Duration()

    @staticmethod
    def _check_is_time_unit(argument):
        argument_type = type(argument)
        if argument_type is not Duration:
            TypeError("Expected to receive " + str(type(Duration)) + " but was " + str(argument_type))

    def __add__(self, other):
        self._check_is_time_unit(other)
        return Duration(self.micros + other.micros)

    def __iadd__(self, other):
        self._check_is_time_unit(other)
        self.micros += other.micros
        return self

    def __sub__(self, other):
        self._check_is_time_unit(other)
        return Duration(self.micros - other.micros)

    def __radd__(self, other):
        self._check_is_time_unit(other)
        self.micros -= other.micros
        return self

    def __gt__(self, other) -> bool:
        self._check_is_time_unit(other)
        return self.micros > other.micros

    def __ge__(self, other) -> bool:
        self._check_is_time_unit(other)
        return self.micros >= other.micros

    def __lt__(self, other) -> bool:
        self._check_is_time_unit(other)
        return self.micros < other.micros

    def __le__(self, other) -> bool:
        self._check_is_time_unit(other)
        return self.micros <= other.micros

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
            string_value += str(seconds) + "s"
        millis = abs(self._hundreds(int(self.millis)))
        if millis != 0:
            string_value += str(millis) + "ms"
        micros = abs(self._hundreds(self.micros))
        if micros != 0:
            string_value += str(micros) + "μs"
        if string_value == "":
            string_value = "zero"
        return "🕒:" + string_value + ""

    @staticmethod
    def _hundreds(value: int):
        return value % (1000 if value > 0 else -1000)


@dataclass
class TimeDelta:
    duration: Duration
    identifier: UUID = None

    def __post_init__(self):
        if self.identifier is None:
            self.identifier = uuid4()


class TimeAffected(ABC):
    @abstractmethod
    def ticked(self, time_delta: TimeDelta): pass


class Constants:
    @staticmethod
    def core() -> Duration:
        pass  # TODO
