from dataclasses import dataclass
from typing import List, Optional
from uuid import uuid4

from bin.sys.time import TimeAffected, Duration, TimeDelta, LogContext


@dataclass
class SystemOperation:
    to_process: bool
    name: str
    duration: Duration

    def __post_init__(self):
        if self.duration.is_zero or self.duration.is_negative:
            raise ValueError('Duration of ' + str(self) + ' should be positive')


class Task(TimeAffected):
    def __init__(
            self,
            operations: List[SystemOperation],
            name: Optional[str] = None
    ):
        if not operations:
            raise ValueError('Task should contain operations')
        self.operations: List[SystemOperation] = operations
        self.name = name if name else "_❔task❔_"
        self._current_operation_processed_time: Duration = Duration.zero()
        self._last_time_delta: Optional[TimeDelta] = None
        self._identifier = uuid4()

    def ticked(self, time_delta: TimeDelta):
        if self.is_complete():
            return
        if self.is_waiting():
            raise ValueError(str(self) + " is waiting but ticked with " + str(time_delta))
        if self._should_skip_same_time_delta_update(time_delta):
            return

        LogContext.logger().log_task_processing(name=self.name, identifier=self._identifier)
        self._increment_time_processing(time_delta)
        self._handle_if_operation_finished()

    def wait(self, time_delta: TimeDelta):
        if self.is_complete():
            return
        if not self.is_waiting():
            raise ValueError(str(self) + " is processing but triggered to wait " + str(time_delta))
        if self._should_skip_same_time_delta_update(time_delta):
            return

        LogContext.logger().log_task_waiting(name=self.name, identifier=self._identifier)
        self._increment_time_waiting(time_delta)
        self._handle_if_operation_finished()

    def is_complete(self) -> bool:
        return not self.operations

    def is_waiting(self) -> bool:
        if not self.operations:
            return True

        return not self._current_operation_is_to_process()

    def _handle_if_operation_finished(self):
        next_operation_time = self._current_operation_processed_time - self._current_operation().duration
        if next_operation_time.is_zero or next_operation_time.is_positive:
            self.operations.pop(0)
            self._current_operation_processed_time = next_operation_time

    def _current_operation(self) -> Optional[SystemOperation]:
        return self.operations[0]

    def _current_operation_is_to_process(self) -> bool:
        current = self._current_operation()
        return current and current.to_process

    def _increment_time_processing(self, delta: TimeDelta):
        if not self._current_operation_is_to_process():
            return
        self._current_operation_processed_time += delta.duration

    def _increment_time_waiting(self, delta: TimeDelta):
        if self._current_operation_is_to_process():
            return
        self._current_operation_processed_time += delta.duration

    def _should_skip_same_time_delta_update(self, delta: TimeDelta) -> bool:
        if self._last_time_delta == delta:
            return True
        self._last_time_delta = delta
        return False

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.name

    def _as_string(self) -> str:
        return self.name + "[" + str(self._identifier) + "]<" + str(self.operations) + ">"
