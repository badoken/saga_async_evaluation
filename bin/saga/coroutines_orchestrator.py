import math
from typing import List

from bin.saga.coroutine_thread import CoroutineThreadFactory, CoroutineThread
from bin.saga.simple_saga import SimpleSaga
from bin.sys.operation_system import OperationSystemFactory, ProcessingMode
from bin.sys.time.duration import Duration


class CoroutinesOrchestrator:
    def __init__(
            self,
            cores_count: int,
            system_factory: OperationSystemFactory = OperationSystemFactory(),
            coroutine_thread_factory: CoroutineThreadFactory = CoroutineThreadFactory()
    ):
        self._cores_count = cores_count
        self._system = system_factory.create(
            cores_count=cores_count,
            processing_mode=ProcessingMode.FIXED_POOL_SIZE
        )
        self._coroutine_factory = coroutine_thread_factory

    def process(self, sagas: List[SimpleSaga]) -> Duration:
        coroutines: List[CoroutineThread] = []

        sagas_bunch_size: int = int(math.ceil(float(len(sagas)) / self._cores_count))
        for i in range(self._cores_count):
            if not sagas:
                break

            if len(sagas) < sagas_bunch_size:
                coroutine = self._coroutine_factory.new(sagas)
                coroutines.append(coroutine)
                break

            coroutine = self._coroutine_factory.new(sagas[:sagas_bunch_size])
            coroutines.append(coroutine)
            sagas = sagas[sagas_bunch_size:]

        self._system.publish(coroutines)
        result = Duration.zero()
        tick_length = Duration(micros=1)

        while not self._system.work_is_done():
            print(str(result) + " {")
            self._system.tick(tick_length)
            result += tick_length
            print("}\n")

        return result
