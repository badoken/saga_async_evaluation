from enum import Enum
from typing import List

from src.sys.core import CoreFactory
from src.sys.thread import Thread
from src.sys.time.time import TimeDelta
from src.log import LogContext
from src.sys.time.duration import Duration


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
        self._to_process_threads_queue: List[Thread] = []
        self._cores = core_factory.new(count=cores_count, processing_interval=Duration(micros=60))
        self._published: List[Thread] = []

    def publish(self, threads: List[Thread]):
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
        self._perform_processing(duration)
        LogContext.shift_time()

    def _perform_processing(self, duration):
        if self.processing_mode is ProcessingMode.FIXED_POOL_SIZE:
            self._feed_starving_cores()
        delta = TimeDelta(duration=duration)
        for core in self._cores:
            core.ticked(time_delta=delta)
        for thread in self._published:
            for current_task in thread.get_current_tasks():
                if not current_task.is_waiting():
                    continue
                current_task.wait(time_delta=delta)

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
