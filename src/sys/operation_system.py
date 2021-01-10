from enum import Enum
from typing import List

from src.sys.processor import ProcessorFactory
from src.sys.thread import Thread
from src.sys.time.time import TimeDelta
from src.sys.time.duration import Duration
from src.sys.time.constants import thread_timeslice


class ProcessingMode(Enum):
    FIXED_POOL_SIZE = 1
    OVERLOADED_PROCESSORS = 2


class OperationSystem:
    def __init__(
            self,
            processors_count: int,
            processing_mode: ProcessingMode,
            proc_factory: ProcessorFactory = ProcessorFactory()
    ):
        self.processing_mode = processing_mode
        self._to_process_threads_queue: List[Thread] = []
        self._processors = proc_factory.new(count=processors_count, processing_interval=thread_timeslice())
        self._published: List[Thread] = []

    def publish(self, threads: List[Thread]):
        self._published = threads
        if self.processing_mode is ProcessingMode.OVERLOADED_PROCESSORS:
            processors_number = len(self._processors)
            for i in range(len(threads)):
                thread = threads[i]
                processor = self._processors[i % processors_number]
                processor.assign(thread)
            return

        self._to_process_threads_queue.extend(threads)
        self._feed_starving_processors()

    def tick(self, time_delta: TimeDelta):
        if self.processing_mode is ProcessingMode.FIXED_POOL_SIZE:
            self._feed_starving_processors()
        for processor in self._processors:
            processor.ticked(time_delta=time_delta)

    def _feed_starving_processors(self):
        if not len(self._to_process_threads_queue):
            return

        for processor in self._processors:
            if not processor.is_starving():
                continue
            if not len(self._to_process_threads_queue):
                return
            thread = self._to_process_threads_queue.pop(0)
            processor.assign(thread)

    def work_is_done(self) -> bool:
        return len(self._to_process_threads_queue) == 0 and \
               all([processor.is_starving() for processor in self._processors])


class OperationSystemFactory:
    # noinspection PyMethodMayBeStatic
    def create(
            self,
            processors_count: int,
            processing_mode: ProcessingMode
    ) -> OperationSystem:
        return OperationSystem(processors_count, processing_mode)
