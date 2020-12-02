from typing import List, Optional

from bin.sys.sys_thread import SysThread
from bin.sys.task import Task
from bin.sys.time import TimeDelta


class SimpleSaga(SysThread):
    def __init__(self, tasks: List[Task], name: str = "unnamed"):
        self._tasks: List[Task] = tasks
        self._processing: bool = False
        self._name = name

    def is_finished(self) -> bool:
        return len(self._tasks) == 0

    def ticked(self, time_delta: TimeDelta):
        current_task = self.get_current_task()
        if not current_task:
            return
        if current_task.is_waiting():
            return

        current_task.processing = self._processing
        print("🚀Saga " + str(self._name) + " triggering " + str(current_task.name) + ". Before: " + str(current_task._current_operation_processed_time) + " is processing " + str(current_task.processing))
        current_task.ticked(time_delta)
        print("🚀Saga " + str(self._name) + " triggered " + str(current_task.name) + ". After: " + str(current_task._current_operation_processed_time) + " is processing " + str(current_task.processing))
        if not current_task.is_complete():
            return

        current_task.processing = False
        self._tasks.pop(0)

    def set_processing(self, is_processing: bool):
        self._processing = is_processing

    def get_current_task(self) -> Optional[Task]:
        return next(iter(self._tasks), None)

    def __str__(self) -> str:
        return self._name

    def __repr__(self):
        return self._name

    def _as_str(self):
        return self._name + " " + str(self._tasks)
