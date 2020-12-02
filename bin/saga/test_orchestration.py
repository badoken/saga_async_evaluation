from typing import Tuple
from unittest import TestCase
from unittest.mock import Mock, call

from bin.saga.orchestration import Orchestrator
from bin.saga.simple_saga import SimpleSaga
from bin.sys.operation_system import OperationSystemFactory, OperationSystem, ProcessingMode
from bin.sys.task import Task, SystemOperation
from bin.sys.time import Duration


class TestOrchestrator(TestCase):
    def test_process(self):
        # given
        cores_factory, system = given_system_factory_that_produces_mock(
            expected_cores=2,
            expected_mode=ProcessingMode.OVERLOADED_CORES
        )
        orchestrator = Orchestrator(
            cores_count=2,
            processing_mode=ProcessingMode.OVERLOADED_CORES,
            system_factory=cores_factory
        )

        work_is_done_answers = [False for _ in range(3)]
        system.tick = Mock(side_effect=lambda duration: work_is_done_answers.pop(0))
        system.publish_task = Mock()

        saga: SimpleSaga = Mock()
        system.work_is_done = lambda: next(iter(work_is_done_answers), True)

        # when
        orchestrator.process(sagas=[saga])

        # then
        system.publish_task([saga])
        system.tick.assert_has_calls(
            calls=[
                call.tick(Duration(micros=1)),
                call.tick(Duration(micros=1)),
                call.tick(Duration(micros=1))
            ]
        )


def create_task(name: str) -> Task:
    task = Task(operations=[SystemOperation(to_process=False, name=name, duration=Duration(2))])
    return task


def given_system_factory_that_produces_mock(expected_cores: int, expected_mode: ProcessingMode) -> \
        Tuple[OperationSystemFactory, OperationSystem]:
    factory = OperationSystemFactory()
    system = Mock()
    factory.create = \
        lambda cores_count, processing_mode: system \
            if cores_count == expected_cores and processing_mode == expected_mode \
            else ValueError("Expected "
                            + str((expected_cores, expected_mode)) +
                            " but was " + str((cores_count, processing_mode))
                            )

    return factory, system
