from enum import Enum
from typing import List

from src.sys.processor import ProcessorFactory
from src.sys.thread import Executable, KernelThread, ChainOfExecutables
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
        self._processors = proc_factory.new(count=processors_count, processing_interval=thread_timeslice())
        self._published: List[Executable] = []

    def publish(self, executables: List[Executable]):
        self._published = executables
        processors_number = len(self._processors)

        if self.processing_mode is ProcessingMode.OVERLOADED_PROCESSORS:
            for i in range(len(executables)):
                executable = executables[i]
                processor = self._processors[i % processors_number]
                thread = KernelThread(executable)
                processor.assign(thread)
            return

        all_executalbe_pools: List[List[Executable]] = [[] for _ in range(processors_number)]
        for i in range(len(executables)):
            executable = executables[i]
            executables_pool = all_executalbe_pools[i % processors_number]
            executables_pool.append(executable)

        for processor_num in range(processors_number):
            executable: Executable = ChainOfExecutables(*all_executalbe_pools.pop(0))
            self._processors[processor_num].assign(KernelThread(executable))

    def tick(self, time_delta: TimeDelta):
        for processor in self._processors:
            processor.ticked(time_delta=time_delta)

    def work_is_done(self) -> bool:
        return all([processor.is_starving() for processor in self._processors])


class SystemFactory:
    # noinspection PyMethodMayBeStatic
    def create(
            self,
            processors_count: int,
            processing_mode: ProcessingMode
    ) -> System:
        return System(processors_count, processing_mode)
