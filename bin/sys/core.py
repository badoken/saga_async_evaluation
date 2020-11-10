from enum import Enum
from typing import List, Optional

from bin.sys.time import TimeAffected

from dataclasses import dataclass

from bin.sys.task import Task


class Mode(Enum):
    ASYNC = 1
    SYNC = 2


@dataclass
class Core(TimeAffected):
    unassigned_tasks_pool: List[Task]
    mode: Mode
    id: int = -1

    def __post_init__(self):
        self._processing = None

    def ticked(self):
        self._configure_current_task()

        if self._processing:
            self._handle_current_task()

    def _handle_current_task(self):
        self._processing.ticked()
        if self._processing.is_complete():
            self._stop_processing_current_task()
        elif self._processing.is_waiting() and self.mode is Mode.ASYNC:
            self.unassigned_tasks_pool.append(self._processing)
            self._stop_processing_current_task()

    def _stop_processing_current_task(self):
        self._processing.processing = False
        self._processing = None

    def _configure_current_task(self):
        if self._processing is not None:
            return

        if not self.unassigned_tasks_pool:
            return
        self._processing = self.unassigned_tasks_pool.pop(0)
        self._processing.processing = True


# noinspection PyMethodMayBeStatic
class CoreFactory:
    def __init__(self):
        self.last_id = 1

    def new(self, count: int, unassigned_tasks_pool: List[Task], mode: Mode) -> List[Core]:
        cores = []
        for i in range(count):
            cores.append(Core(unassigned_tasks_pool, mode, id=self.last_id))
        return cores
