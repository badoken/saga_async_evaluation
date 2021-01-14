from typing import List, Optional

from src.sys.thread import Executable
from src.saga.task import Task
from src.sys.time.time import TimeDelta


class CoroutineSaga(Executable):
    def __init__(self, executables: List[Executable], name: str = "_❔coroutine❔_"):
        if any([type(executable) is CoroutineSaga for executable in executables]):
            raise ValueError("Coroutine executable specified as input for a new coroutine")
        self._executables: List[Executable] = executables
        self._name = name

    def is_finished(self) -> bool:
        return self._get_current_executable() is None

    def get_current_tasks(self) -> List[Task]:
        tasks: List[Task] = []
        for executable in self._executables:
            tasks = tasks + executable.get_current_tasks()
        return tasks

    def ticked(self, time_delta: TimeDelta):
        if self.is_finished():
            return

        for i in range(len(self._executables)):
            executable = self._get_current_executable()
            if self._handle_if_finished(executable):
                continue

            if all([task.is_waiting() for task in executable.get_current_tasks()]):
                self._executables.append(
                    self._executables.pop(0)
                )
                continue

            executable.ticked(time_delta=time_delta)
            self._handle_if_finished(executable)
            return

    def _handle_if_finished(self, executable) -> bool:
        if not executable.is_finished():
            return False
        self._executables.pop(0)
        return True

    def _get_current_executable(self) -> Optional[Executable]:
        return next(iter(self._executables), None)

    def __str__(self) -> str:
        return self._name

    def __repr__(self):
        return self._name

    def _as_str(self):
        return f"{self._name}<{self._executables}>"


class CoroutineSagaFactory:
    def __init__(self):
        self.last_id = -1

    def new(
            self,
            executables: List[Executable]
    ) -> CoroutineSaga:
        self.last_id += 1
        return CoroutineSaga(executables=executables, name=f"coroutine{self.last_id}")
