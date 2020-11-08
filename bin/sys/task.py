from dataclasses import dataclass
from typing import List, Optional

from bin.sys.system import TimeAffected, TimeUnit


@dataclass
class SystemOperation:
    to_process: bool
    name: str
    duration: TimeUnit

    def __post_init__(self):
        if self.duration.val <= 0:
            raise ValueError('Duration of ' + str(self) + ' should be positive')


@dataclass
class Task(TimeAffected):
    operations: List[SystemOperation]
    processing: bool = False

    def __post_init__(self):
        if not self.operations:
            raise ValueError('Task should contain operations')
        self.current_operation_duration = TimeUnit(0)

    def ticked(self):
        if not self.operations:
            return

        self._increment_time()

        next_operation_time = self.current_operation_duration.val - self._current_operation().duration.val
        if next_operation_time >= 0:
            self.operations.pop(0)
            # noinspection PyAttributeOutsideInit
            self.current_operation_duration = TimeUnit(next_operation_time)

    def is_complete(self) -> bool:
        return not self.operations

    def is_waiting(self) -> bool:
        if not self.processing or not self.operations:
            return True

        return not self._current_operation().to_process

    def _current_operation(self) -> Optional[SystemOperation]:
        return self.operations[0]

    def _current_operation_is_to_process(self) -> bool:
        current = self._current_operation()
        return current and current.to_process

    def _increment_time(self):
        if not self.processing and self._current_operation_is_to_process():
            return

        self.current_operation_duration.increment()
