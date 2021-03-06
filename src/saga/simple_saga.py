from typing import List, Optional

from src.sys.thread import Executable
from src.saga.task import Task
from src.sys.time.time import TimeDelta


class SimpleSaga(Executable):
    def __init__(self, tasks: List[Task], name: str = "unnamed"):
        self._tasks: List[Task] = tasks
        self._processing: bool = False
        self._name = name

    def is_finished(self) -> bool:
        return len(self._tasks) == 0

    def ticked(self, time_delta: TimeDelta):
        current_task = self._get_current_task()
        if not current_task:
            return
        if current_task.is_waiting():
            return

        current_task.ticked(time_delta)

        if not current_task.is_complete():
            return

        self._tasks.pop(0)

    def get_current_tasks(self) -> List[Task]:
        current_task = self._get_current_task()
        return [current_task] if current_task else []

    def _get_current_task(self) -> Optional[Task]:
        return next(iter(self._tasks), None)

    def __str__(self) -> str:
        return self._name

    def __repr__(self):
        return self._name

    def _as_str(self):
        return f"{self._name}<{self._tasks}>"
