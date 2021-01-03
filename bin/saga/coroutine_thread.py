from typing import List, Optional

from bin.sys.sys_thread import SysThread
from bin.saga.task.task import Task
from bin.sys.time.time import TimeDelta


class CoroutineThread(SysThread):
    def __init__(self, threads: List[SysThread], name: str = "_❔coroutine❔_"):
        if any([type(thread) is CoroutineThread for thread in threads]):
            raise ValueError("Coroutine thread specified as input for a new coroutine")
        self._threads: List[SysThread] = threads
        self._name = name

    def is_finished(self) -> bool:
        return self._get_current_thread() is None

    def get_current_tasks(self) -> List[Task]:
        tasks: List[Task] = []
        for thread in self._threads:
            tasks = tasks + thread.get_current_tasks()
        return tasks

    def ticked(self, time_delta: TimeDelta):
        if self.is_finished():
            return

        for i in range(len(self._threads)):
            thread = self._get_current_thread()
            if self._handle_if_finished(thread):
                continue

            if all([task.is_waiting() for task in thread.get_current_tasks()]):
                self._threads.append(
                    self._threads.pop(0)
                )
                continue

            thread.ticked(time_delta=time_delta)
            self._handle_if_finished(thread)
            return

        print(self._name + " was unable to trigger any thread. Threads: " +
              str([str(thread) for thread in self._threads]))
        return

    def _handle_if_finished(self, thread) -> bool:
        if not thread.is_finished():
            return False
        self._threads.pop(0)
        return True

    def _get_current_thread(self) -> Optional[SysThread]:
        return next(iter(self._threads), None)

    def __str__(self) -> str:
        return self._name

    def __repr__(self):
        return self._name

    def _as_str(self):
        return self._name + "<" + str(self._threads) + ">"


class CoroutineThreadFactory:
    def __init__(self):
        self.last_id = -1

    def new(
            self,
            threads: List[SysThread]
    ) -> CoroutineThread:
        self.last_id += 1
        return CoroutineThread(threads=threads, name="coroutine" + str(self.last_id))
