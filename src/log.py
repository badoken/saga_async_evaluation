import csv
import threading
from enum import Enum
from threading import local
from typing import Dict, Set, Optional, Callable, TypeVar, OrderedDict
from uuid import UUID


class _LogAction(Enum):
    WAITING = 1
    PROCESSING = 2


class TimeLogger:
    def __init__(self, name: str):
        self._csv_file = open(file=name + '.csv', mode="w")
        self._writer = csv.writer(self._csv_file)

        self._known_identifiers: Set[str] = set()
        self._row: OrderedDict[str, str]
        self._row_number: int = 0
        self._init_new_row()

    def close(self):
        self.shift_time()
        self._csv_file.close()

    def shift_time(self):
        identifiers_to_add = self._known_identifiers.difference(self._row.keys())
        self._row.update(
            dict(
                zip(
                    identifiers_to_add,
                    [0 for _ in range(len(identifiers_to_add))]
                )
            )
        )

        self._writer.writerow(self._row.values())
        self._init_new_row()

    def log_core_tick(self, identifier: int):
        self._log(identifier="core{" + str(identifier) + "}", action=_LogAction.PROCESSING)

    def log_task_processing(self, name: str, identifier: UUID):
        self._log(identifier=self._task_name(identifier, name), action=_LogAction.PROCESSING)

    def log_task_waiting(self, name: str, identifier: UUID):
        self._log(identifier=self._task_name(identifier, name), action=_LogAction.WAITING)

    def _log(self, identifier: str, action: _LogAction):
        if identifier in self._row is not None:
            raise ValueError("At this point of time there is a record for " + identifier + " already")

        self._known_identifiers.add(identifier)
        self._row[identifier] = action.value

    def _init_new_row(self):
        self._row_number += 1
        self._row = OrderedDict[str, str]()
        self._row["microseconds"] = str(self._row_number)

    @staticmethod
    def _task_name(identifier, name):
        return "t{" + name + "}[" + str(identifier) + "]"


class LogContext:
    _lock = threading.Lock()
    _logger: Dict[int, TimeLogger] = {}
    T = TypeVar('T')

    @staticmethod
    def run_logging(log_name: str, action: Callable[[], T]) -> T:
        with LogContext._lock:
            LogContext._logger[threading.get_ident()] = TimeLogger(name=log_name)

        print("Running log in " + str(threading.get_ident()) + " and logger is " + (
            str(LogContext._logger) if hasattr(LogContext, "_logger") and LogContext._logger is not None else "None"))

        try:
            result = action()
        finally:
            with LogContext._lock:
                LogContext.logger().close()
                LogContext._logger.pop(threading.get_ident())

        return result

    @staticmethod
    def logger() -> Optional[TimeLogger]:
        # with LogContext._lock:
        return LogContext._logger.get(threading.get_ident())

    @staticmethod
    def shift_time():
        LogContext.logger().shift_time()
