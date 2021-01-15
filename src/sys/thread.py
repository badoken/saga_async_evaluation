from abc import abstractmethod
from typing import List

from src.saga.task import Task
from src.sys.time.constants import thread_creation_cost, thread_destruction_cost
from src.sys.time.time import TimeAffected, Limited
from src.sys.time.time import TimeDelta


class Executable(TimeAffected, Limited):
    @abstractmethod
    def get_current_tasks(self) -> List[Task]: pass


class KernelThread(TimeAffected, Limited):
    def __init__(self, executable: Executable):
        self._executable = executable
        self._init_cool_down = thread_creation_cost()
        self._destruct_cool_down = thread_destruction_cost()

    def is_doing_system_operation(self) -> bool:
        if self._init_cool_down.is_positive:
            return True
        if self._executable.is_finished() and self._destruct_cool_down.is_positive:
            return True
        return False

    def ticked(self, time_delta: TimeDelta):
        if self._init_cool_down.is_positive:
            self._init_cool_down -= time_delta.duration
            return

        if not self._executable.is_finished():
            self._executable.ticked(time_delta)
            return

        if self._destruct_cool_down.is_positive:
            self._destruct_cool_down -= time_delta.duration
            return

    def is_finished(self) -> bool:
        return not self._destruct_cool_down.is_positive
