from typing import Tuple
from unittest import TestCase
from unittest.mock import Mock, call

from src.saga.threaded_orchestrator import ThreadedOrchestrator
from src.saga.simple_saga import SimpleSaga
from src.sys.operation_system import OperationSystemFactory, OperationSystem, ProcessingMode
from src.saga.task import Task, SystemOperation
from src.sys.time.duration import Duration


class TestThreadedOrchestrator(TestCase):
    def test_process(self):
        # given
        cores_factory, system = given_system_factory_that_produces_mock(
            expected_cores=2,
            expected_mode=ProcessingMode.OVERLOADED_CORES
        )
        orchestrator = ThreadedOrchestrator(
            cores_count=2,
            processing_mode=ProcessingMode.OVERLOADED_CORES,
            system_factory=cores_factory
        )

        work_is_done_answers = [False for _ in range(3)]
        system.tick = Mock(side_effect=lambda duration: work_is_done_answers.pop(0))
        system.publish = Mock()

        saga: SimpleSaga = Mock()
        system.work_is_done = lambda: next(iter(work_is_done_answers), True)

        # when
        orchestrator.process(sagas=[saga])

        # then
        system.publish.assert_called_once_with([saga])
        system.tick.assert_has_calls(
            calls=[
                call.tick(Duration(nanos=1)),
                call.tick(Duration(nanos=1)),
                call.tick(Duration(nanos=1))
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
            else ValueError(f"Expected {(expected_cores, expected_mode)}" +
                            f" but was {(cores_count, processing_mode)}")

    return factory, system
