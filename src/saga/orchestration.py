import math
from typing import List

from src.saga.coroutine_thread import CoroutineThreadFactory, CoroutineThread
from src.saga.simple_saga import SimpleSaga
from src.sys.operation_system import OperationSystemFactory, ProcessingMode, OperationSystem
from src.sys.time.duration import Duration
from src.sys.thread import Thread


def _run_threads(sagas: List[Thread], os: OperationSystem) -> Duration:
    os.publish(sagas)
    result = Duration.zero()
    tick_length = Duration(nanos=1)

    while not os.work_is_done():
        os.tick(tick_length)
        result += tick_length

    return result


class ThreadedOrchestrator:
    def __init__(
            self,
            processors_number: int,
            processing_mode: ProcessingMode,
            os_factory: OperationSystemFactory = OperationSystemFactory()
    ):
        self._os = os_factory.create(
            processors_count=processors_number,
            processing_mode=processing_mode
        )

    def process(self, sagas: List[SimpleSaga]) -> Duration:
        return _run_threads(sagas=sagas, os=self._os)


class CoroutinesOrchestrator:
    def __init__(
            self,
            processors_number: int,
            os_factory: OperationSystemFactory = OperationSystemFactory(),
            coroutine_thread_factory: CoroutineThreadFactory = CoroutineThreadFactory()
    ):
        self._processors_count = processors_number
        self._os = os_factory.create(
            processors_count=processors_number,
            processing_mode=ProcessingMode.FIXED_POOL_SIZE
        )
        self._coroutine_factory = coroutine_thread_factory

    def process(self, sagas: List[SimpleSaga]) -> Duration:
        coroutines: List[CoroutineThread] = []

        sagas_bunch_size: int = int(math.ceil(float(len(sagas)) / self._processors_count))
        for i in range(self._processors_count):
            if not sagas:
                break

            if len(sagas) < sagas_bunch_size:
                coroutine = self._coroutine_factory.new(sagas)
                coroutines.append(coroutine)
                break

            coroutine = self._coroutine_factory.new(sagas[:sagas_bunch_size])
            coroutines.append(coroutine)
            sagas = sagas[sagas_bunch_size:]

        return _run_threads(sagas=coroutines, os=self._os)
