from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Optional, Any
from uuid import UUID, uuid4

import xlsxwriter


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


class TimeLogger:
    def __init__(self, name: str):
        self._workbook = xlsxwriter.Workbook(filename=name + '.xlsx')
        self._sheet = self._workbook.add_worksheet(name=name)
        self._sheet.write(0, 0, "An operation name")
        self._sheet.write(0, 2, "A core operation duration")
        self._sheet.write(0, 3, "A task processing duration")
        self._sheet.write(0, 4, "A task wait duration")
        self._row = 1

    def close(self):
        self._workbook.close()

    def log_core_tick(self, time_delta: TimeDelta, identifier: int):
        row = self._get_row_and_increment()
        self._sheet.write(row, 0, 'core' + str(identifier))
        self._sheet.write(row, 2, str(time_delta.duration.micros))

    def log_task_processing(self, time_delta: TimeDelta, name: str):
        row = self._get_row_and_increment()
        self._sheet.write(row, 0, name)
        self._sheet.write(row, 3, str(time_delta.duration.micros))

    def log_task_waiting(self, time_delta: TimeDelta, name: str):
        row = self._get_row_and_increment()
        self._sheet.write(row, 0, name)
        self._sheet.write(row, 4, str(time_delta.duration.micros))

    def _get_row_and_increment(self) -> int:
        result = self._row
        self._row = result + 1
        return result


class LogContext:
    _logger: Optional[TimeLogger] = None

    @staticmethod
    def run_logging(log_name: str, action: Callable[[], Any]):
        LogContext._logger = TimeLogger(name=log_name)
        action()
        LogContext._logger.close()
        LogContext._logger = None

    @staticmethod
    def logger() -> Optional[TimeLogger]:
        return LogContext._logger
