from typing import Tuple
from unittest import TestCase
from unittest.mock import Mock, call

from bin.saga.coroutine_thread import CoroutineThreadFactory, CoroutineThread
from bin.saga.coroutines_orchestrator import CoroutinesOrchestrator
from bin.saga.simple_saga import SimpleSaga
from bin.sys.operation_system import OperationSystemFactory, OperationSystem, ProcessingMode
from bin.saga.task.task import Task, SystemOperation
from bin.sys.time.duration import Duration


class TestCoroutinesOrchestrator(TestCase):
    def test_process_when_the_number_of_sagas_is_greater_then_the_number_of_cores(self):
        # given
        cores_factory, system = given_system_factory_that_produces_mock(
            expected_cores=2,
            expected_mode=ProcessingMode.FIXED_POOL_SIZE
        )
        coroutine_factory: CoroutineThreadFactory = Mock()
        orchestrator = CoroutinesOrchestrator(
            cores_count=2,
            system_factory=cores_factory,
            coroutine_thread_factory=coroutine_factory
        )
        saga1: SimpleSaga = Mock()
        saga2: SimpleSaga = Mock()
        saga3: SimpleSaga = Mock()

        coroutine1 = given_factory_will_return_coroutine_for(factory=coroutine_factory, sagas=[saga1, saga2])
        coroutine2 = given_factory_will_return_coroutine_for(factory=coroutine_factory, sagas=[saga3])

        work_is_done_answers = [False for _ in range(3)]
        system.tick = Mock(side_effect=lambda duration: work_is_done_answers.pop(0))
        system.publish = Mock()

        system.work_is_done = lambda: next(iter(work_is_done_answers), True)

        # when
        orchestrator.process(sagas=[saga1, saga2, saga3])

        # then
        system.publish.assert_called_once_with([coroutine1, coroutine2])
        system.tick.assert_has_calls(
            calls=[
                call.tick(Duration(micros=1)),
                call.tick(Duration(micros=1)),
                call.tick(Duration(micros=1))
            ]
        )

    def test_process_when_the_number_of_sagas_is_lesser_then_the_number_of_cores(self):
        # given
        cores_factory, system = given_system_factory_that_produces_mock(
            expected_cores=2,
            expected_mode=ProcessingMode.FIXED_POOL_SIZE
        )
        coroutine_factory: CoroutineThreadFactory = Mock()
        orchestrator = CoroutinesOrchestrator(
            cores_count=2,
            system_factory=cores_factory,
            coroutine_thread_factory=coroutine_factory
        )
        saga1: SimpleSaga = Mock()

        coroutine1 = given_factory_will_return_coroutine_for(factory=coroutine_factory, sagas=[saga1])

        work_is_done_answers = [False for _ in range(3)]
        system.tick = Mock(side_effect=lambda duration: work_is_done_answers.pop(0))
        system.publish = Mock()

        system.work_is_done = lambda: next(iter(work_is_done_answers), True)

        # when
        orchestrator.process(sagas=[saga1])

        # then
        system.publish.assert_called_once_with([coroutine1])
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


def given_factory_will_return_coroutine_for(factory: CoroutineThreadFactory, sagas: [SimpleSaga]) -> CoroutineThread:
    coroutine: CoroutineThread = Mock()

    previous_factory_function = factory.new
    factory.new = lambda threads: coroutine if sagas == threads else previous_factory_function(threads)

    return coroutine
