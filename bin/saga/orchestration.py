from copy import copy, deepcopy
from dataclasses import dataclass
from enum import Enum
from typing import List

from bin.saga.saga import Saga
from bin.sys.core import Mode
from bin.sys.system import System, SystemFactory
from bin.sys.task import Task


class Orchestrator:
    def __init__(self, cores_count: int, processing_mode: Mode, system_factory: SystemFactory = SystemFactory()):
        self._system = system_factory.create(
            cores_count=cores_count,
            processing_mode=processing_mode
        )

    def process(self, sagas: List[Saga]):
        _sagas = deepcopy(sagas)
        executions: List[SagaExecution] = []
        for saga in _sagas:
            executions.append(SagaExecution(saga, saga.last_incomplete_task()))

        for execution in executions:
            self._system.publish_task(execution.current_task)

        while executions:
            self._system.tick()
            for execution in executions:
                result = execution.refresh()
                if result is RefreshResult.FINISHED:
                    executions.remove(execution)
                elif result is RefreshResult.IN_PROGRESS:
                    continue
                else:
                    self._system.publish_task(execution.current_task)


class RefreshResult(Enum):
    FINISHED = 0
    UPDATED = 1
    IN_PROGRESS = 2


@dataclass
class SagaExecution:
    saga: Saga
    current_task: Task

    def refresh(self) -> RefreshResult:
        last_incomplete_task = self.saga.last_incomplete_task()
        if last_incomplete_task is None:
            return RefreshResult.FINISHED
        if last_incomplete_task is not self.current_task:
            self.current_task = last_incomplete_task
            return RefreshResult.UPDATED
        if last_incomplete_task is self.current_task:
            return RefreshResult.IN_PROGRESS
