from enum import Enum
from typing import Dict, Set, Optional, Callable, Any, TypeVar
from uuid import UUID

from xlsxwriter import Workbook


class _LogAction(Enum):
    WAITING = 1
    PROCESSING = 2


class TimeLogger:
    def __init__(self, name: str):
        self._workbook = Workbook(filename=name + '.xlsx')
        self._sheet = self._workbook.add_worksheet(name=name)

        self._id_to_column: Dict[str, int] = {}
        self._already_used_columns: Set[int] = set()
        self._row = 1

    def close(self):
        self.shift_time()

        for i, key in enumerate(self._id_to_column.keys()):
            self._sheet.write(0, i + 1, key)

        self._workbook.close()

    def shift_time(self):
        self._sheet.write(self._row, 0, self._row)
        for untouched_column in (
                set(self._id_to_column.values()) -
                self._already_used_columns
        ):
            self._sheet.write(self._row, untouched_column, 0)

        self._row = self._row + 1
        self._already_used_columns = set()

    def log_core_tick(self, identifier: int):
        self._log(identifier="core{" + str(identifier) + "}", action=_LogAction.PROCESSING)

    def log_task_processing(self, name: str, identifier: UUID):
        self._log(identifier=self._task_name(identifier, name), action=_LogAction.PROCESSING)

    def log_task_waiting(self, name: str, identifier: UUID):
        self._log(identifier=self._task_name(identifier, name), action=_LogAction.WAITING)

    def _log(self, identifier: str, action: _LogAction):
        column = self._id_to_column.get(identifier)
        if not column:
            occupied_columns = list(self._id_to_column.values())
            occupied_columns.sort(reverse=True)
            column = next(iter(occupied_columns), 0) + 1
            self._id_to_column[identifier] = column

        if column in self._already_used_columns:
            raise ValueError("At this point of time there is a record for " + identifier + " already")
        self._already_used_columns.add(column)

        self._sheet.write(self._row, column, action.value)

    @staticmethod
    def _task_name(identifier, name):
        return "t{" + name + "}[" + str(identifier) + "]"


class LogContext:
    _logger: Optional[TimeLogger] = None
    T = TypeVar('T')

    @staticmethod
    def run_logging(log_name: str, action: Callable[[], T]) -> T:
        LogContext._logger = TimeLogger(name=log_name)

        result = action()

        LogContext._logger.close()
        LogContext._logger = None

        return result

    @staticmethod
    def logger() -> Optional[TimeLogger]:
        return LogContext._logger

    @staticmethod
    def shift_time():
        LogContext.logger().shift_time()
