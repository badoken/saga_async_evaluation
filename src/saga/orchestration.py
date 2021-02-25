from math import ceil
from abc import ABC, abstractmethod
from typing import List

from src.log import LogContext
from src.saga.coroutine_saga import CoroutineSagaFactory, CoroutineSaga
from src.saga.simple_saga import SimpleSaga
from src.sys.system import SystemFactory, ProcessingMode, System
from src.sys.time.duration import Duration
from src.sys.thread import Executable
from src.sys.time.time import TimeDelta


def _run(executables: List[Executable], system: System) -> Duration:
    system.publish(executables)
    result = Duration.zero()
    tick_length = Duration(micros=1)

    while not system.work_is_done():
        delta = TimeDelta(duration=tick_length)
        system.tick(delta)
        result += tick_length

        for executable in executables:
            for current_task in executable.get_current_tasks():
                if not current_task.is_waiting():
                    continue
                current_task.wait(time_delta=delta)

        LogContext.shift_time()

    return result


class Orchestrator(ABC):
    @abstractmethod
    def process(self, sagas: List[SimpleSaga]) -> Duration:
        pass

    @abstractmethod
    def name(self) -> str:
        pass


class ThreadedOrchestrator(Orchestrator):
    def __init__(
            self,
            processors_number: int,
            processing_mode: ProcessingMode,
            system_factory: SystemFactory = SystemFactory()
    ):
        self._system = system_factory.create(
            processors_count=processors_number,
            processing_mode=processing_mode
        )
        self.processing_mode = processing_mode

    def process(self, sagas: List[SimpleSaga]) -> Duration:
        return _run(executables=sagas, system=self._system)

    def name(self) -> str:
        return f"threaded_orchestrator_in_{self.processing_mode}_mode"


class CoroutinesOrchestrator(Orchestrator):
    def __init__(
            self,
            processors_number: int,
            system_factory: SystemFactory = SystemFactory(),
            coroutine_saga_factory: CoroutineSagaFactory = CoroutineSagaFactory()
    ):
        self._processors_number = processors_number
        self._system = system_factory.create(
            processors_count=processors_number,
            processing_mode=ProcessingMode.FIXED_POOL_SIZE
        )
        self._coroutine_factory = coroutine_saga_factory

    def process(self, sagas: List[SimpleSaga]) -> Duration:
        coroutines: List[CoroutineSaga] = []

        sagas_bunch_size: int = int(ceil(float(len(sagas)) / self._processors_number))
        for i in range(self._processors_number):
            if not sagas:
                break

            if len(sagas) < sagas_bunch_size:
                coroutine = self._coroutine_factory.new(sagas)
                coroutines.append(coroutine)
                break

            coroutine = self._coroutine_factory.new(sagas[:sagas_bunch_size])
            coroutines.append(coroutine)
            sagas = sagas[sagas_bunch_size:]

        return _run(executables=coroutines, system=self._system)

    def name(self) -> str:
        return f"coroutines_orchestrator"
