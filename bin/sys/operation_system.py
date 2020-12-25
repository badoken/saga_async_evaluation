from enum import Enum
from typing import List
from uuid import UUID, uuid4, uuid5

from bin.sys.core import CoreFactory
from bin.sys.sys_thread import SysThread
from bin.sys.time import Duration, TimeDelta


class ProcessingMode(Enum):
    FIXED_POOL_SIZE = 1
    OVERLOADED_CORES = 2


class OperationSystem:
    def __init__(
            self,
            cores_count: int,
            processing_mode: ProcessingMode,
            core_factory: CoreFactory = CoreFactory()
    ):
        self.processing_mode = processing_mode
        self._to_process_threads_queue: List[SysThread] = []
        self._cores = core_factory.new(count=cores_count, processing_interval=Duration(micros=60))
        self._published: List[SysThread] = []

    def publish(self, threads: List[SysThread]):
        self._published = threads
        if self.processing_mode is ProcessingMode.OVERLOADED_CORES:
            cores_number = len(self._cores)
            for i in range(len(threads)):
                thread = threads[i]
                core = self._cores[i % cores_number]
                core.assign(thread)
            return

        self._to_process_threads_queue.extend(threads)
        self._feed_starving_cores()

    def tick(self, duration: Duration):
        if self.processing_mode is ProcessingMode.FIXED_POOL_SIZE:
            self._feed_starving_cores()

        delta = TimeDelta(duration=duration)
        for core in self._cores:
            print("Triggering core " + str(core))
            core.ticked(time_delta=delta)
        for thread in self._published:
            for current_task in thread.get_current_tasks():
                if not current_task.is_waiting():
                    continue

                print("Triggering wait on task " + str(current_task.name) +
                      ". Before: " + str(current_task._current_operation_processed_time))

                current_task.wait(time_delta=delta)

                print("Triggering wait on task " + str(current_task.name) +
                      ". After: " + str(current_task._current_operation_processed_time))

    def _feed_starving_cores(self):
        if not len(self._to_process_threads_queue):
            return

        for core in self._cores:
            if not core.is_starving():
                continue
            if not len(self._to_process_threads_queue):
                return
            thread = self._to_process_threads_queue.pop(0)
            core.assign(thread)

    def work_is_done(self) -> bool:
        return len(self._to_process_threads_queue) == 0 and all([core.is_starving() for core in self._cores])


class OperationSystemFactory:
    # noinspection PyMethodMayBeStatic
    def create(
            self,
            cores_count: int,
            processing_mode: ProcessingMode
    ) -> OperationSystem:
        return OperationSystem(cores_count, processing_mode)
