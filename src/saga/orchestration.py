import math
from typing import List

from src.log import LogContext
from src.saga.coroutine_thread import CoroutineThreadFactory, CoroutineThread
from src.saga.simple_saga import SimpleSaga
from src.sys.operation_system import OperationSystemFactory, ProcessingMode, OperationSystem
from src.sys.time.duration import Duration
from src.sys.thread import Thread
from src.sys.time.time import TimeDelta


def _run_threads(threads: List[Thread], os: OperationSystem) -> Duration:
    os.publish(threads)
    result = Duration.zero()
    tick_length = Duration(nanos=1)

    while not os.work_is_done():
        delta = TimeDelta(duration=tick_length)
        os.tick(delta)
        result += tick_length

        for thread in threads:
            for current_task in thread.get_current_tasks():
                if not current_task.is_waiting():
                    continue
                current_task.wait(time_delta=delta)

        LogContext.shift_time()

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
        return _run_threads(threads=sagas, os=self._os)


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

        return _run_threads(threads=coroutines, os=self._os)
