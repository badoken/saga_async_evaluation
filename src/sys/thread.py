from __future__ import annotations

from abc import abstractmethod
from typing import List, Optional

from src.log import LogContext
from src.saga.task import Task
from src.sys.time.constants import thread_creation_cost, thread_deallocation_cost
from src.sys.time.time import TimeAffected, Limited
from src.sys.time.time import TimeDelta


class Executable(TimeAffected, Limited):
    @abstractmethod
    def get_current_tasks(self) -> List[Task]: pass


class ChainOfExecutables(Executable):
    def __init__(self, *executables: Executable):
        self._executables = list(executables)

    def get_current_tasks(self) -> List[Task]:
        current = self._current_executable()
        if current is None:
            return []
        return current.get_current_tasks()

    def ticked(self, time_delta: TimeDelta):
        current = self._current_executable()
        if current is None:
            return
        current.ticked(time_delta)

        if current.is_finished():
            self._executables.pop(0)

    def is_finished(self) -> bool:
        return self._current_executable() is None

    def _current_executable(self) -> Optional[Executable]:
        return next(iter(self._executables), None)

    def __eq__(self, other: ChainOfExecutables) -> bool:
        if not isinstance(other, type(self)):
            return False
        return self._executables == other._executables


class KernelThread(TimeAffected, Limited):
    def __init__(self, executable: Executable):
        self._executable = executable
        self._init_cool_down = thread_creation_cost()
        self._destruct_cool_down = thread_deallocation_cost()

    def is_doing_system_operation(self) -> bool:
        if self._init_cool_down.is_positive:
            return True
        if self._executable.is_finished() and self._destruct_cool_down.is_positive:
            return True
        return False

    def can_yield(self) -> bool:
        if self.is_finished() or self.is_doing_system_operation():
            return False

        current_task: Optional[Task] = next(iter(self._executable.get_current_tasks()), None)
        if not current_task:
            return False
        return current_task.is_waiting()

    def ticked(self, time_delta: TimeDelta):
        if self._init_cool_down.is_positive:
            LogContext.logger().log_overhead_tick()
            self._init_cool_down -= time_delta.duration
            return

        if not self._executable.is_finished():
            self._executable.ticked(time_delta)
            return

        if self._destruct_cool_down.is_positive:
            LogContext.logger().log_overhead_tick()
            self._destruct_cool_down -= time_delta.duration
            return

    def is_finished(self) -> bool:
        return not self._destruct_cool_down.is_positive

    def __eq__(self, other: KernelThread):
        if not isinstance(other, type(self)):
            return False

        return self._executable == other._executable and \
               self._init_cool_down == other._init_cool_down and \
               self._destruct_cool_down == other._destruct_cool_down
