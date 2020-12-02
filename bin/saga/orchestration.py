from copy import deepcopy
from typing import List

from bin.saga.simple_saga import SimpleSaga
from bin.sys.operation_system import OperationSystemFactory, ProcessingMode
from bin.sys.time import Duration


class Orchestrator:
    def __init__(
            self,
            cores_count: int,
            processing_mode: ProcessingMode,
            system_factory: OperationSystemFactory = OperationSystemFactory()
    ):
        self._system = system_factory.create(
            cores_count=cores_count,
            processing_mode=processing_mode
        )

    def process(self, sagas: List[SimpleSaga]) -> Duration:
        self._system.publish(sagas)
        result = Duration.zero()
        tick_length = Duration(micros=1)

        while not self._system.work_is_done():
            print(str(result) + " {")
            self._system.tick(tick_length)
            result += tick_length
            print("}\n")

        return result
