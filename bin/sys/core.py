from enum import Enum
from typing import List, Optional

from bin.sys.system import TimeAffected

from dataclasses import dataclass

from bin.sys.task import Task


class Mode(Enum):
    ASYNC = 1
    SYNC = 2


@dataclass
class Core(TimeAffected):
    tasks_pool: List[Task]
    mode: Mode
    processing: Optional[Task] = None

    def ticked(self):
        self._assign_new_task()

        if self.processing:
            self._handle_current_task()

    def _handle_current_task(self):
        self.processing.ticked()
        if self.processing.is_complete():
            self._stop_processing_current_task()
        elif self.processing.is_waiting() and self.mode is Mode.ASYNC:
            self.tasks_pool.append(self.processing)
            self._stop_processing_current_task()

    def _stop_processing_current_task(self):
        self.processing.processing = False
        self.processing = None

    def _assign_new_task(self):
        if not self.tasks_pool:
            return
        self.processing = self.tasks_pool.pop(0)
        self.processing.processing = True
        return
