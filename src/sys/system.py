from enum import Enum
from typing import List

from src.sys.processor import ProcessorFactory
from src.sys.thread import Executable, KernelThread
from src.sys.time.constants import thread_timeslice
from src.sys.time.time import TimeDelta


class ProcessingMode(Enum):
    FIXED_POOL_SIZE = 1
    OVERLOADED_PROCESSORS = 2


class System:
    def __init__(
            self,
            processors_count: int,
            processing_mode: ProcessingMode,
            proc_factory: ProcessorFactory = ProcessorFactory()
    ):
        self.processing_mode = processing_mode
        self._executables_to_process_queue: List[Executable] = []
        self._processors = proc_factory.new(count=processors_count, processing_interval=thread_timeslice())
        self._published: List[Executable] = []

    def publish(self, executables: List[Executable]):
        self._published = executables
        if self.processing_mode is ProcessingMode.OVERLOADED_PROCESSORS:
            processors_number = len(self._processors)
            for i in range(len(executables)):
                executable = executables[i]
                processor = self._processors[i % processors_number]
                thread = KernelThread(executable)
                processor.assign(thread)
            return

        self._executables_to_process_queue.extend(executables)
        self._feed_starving_processors()

    def tick(self, time_delta: TimeDelta):
        if self.processing_mode is ProcessingMode.FIXED_POOL_SIZE:
            self._feed_starving_processors()
        for processor in self._processors:
            processor.ticked(time_delta=time_delta)

    def _feed_starving_processors(self):
        if not len(self._executables_to_process_queue):
            return

        for processor in self._processors:
            if not processor.is_starving():
                continue
            if not len(self._executables_to_process_queue):
                return
            executable = self._executables_to_process_queue.pop(0)
            thread = KernelThread(executable)
            processor.assign(thread)

    def work_is_done(self) -> bool:
        return len(self._executables_to_process_queue) == 0 and \
               all([processor.is_starving() for processor in self._processors])


class SystemFactory:
    # noinspection PyMethodMayBeStatic
    def create(
            self,
            processors_count: int,
            processing_mode: ProcessingMode
    ) -> System:
        return System(processors_count, processing_mode)
