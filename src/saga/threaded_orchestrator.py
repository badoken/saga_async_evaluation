from typing import List

from src.saga.simple_saga import SimpleSaga
from src.sys.operation_system import OperationSystemFactory, ProcessingMode
from src.sys.time.duration import Duration


class ThreadedOrchestrator:
    def __init__(
            self,
            processors_number: int,
            processing_mode: ProcessingMode,
            system_factory: OperationSystemFactory = OperationSystemFactory()
    ):
        self._system = system_factory.create(
            processors_count=processors_number,
            processing_mode=processing_mode
        )

    def process(self, sagas: List[SimpleSaga]) -> Duration:
        self._system.publish(sagas)
        result = Duration.zero()
        tick_length = Duration(nanos=1)

        while not self._system.work_is_done():
            self._system.tick(tick_length)
            result += tick_length

        return result
