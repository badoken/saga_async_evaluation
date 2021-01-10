from typing import Tuple
from unittest import TestCase
from unittest.mock import Mock, call

from src.saga.coroutine_thread import CoroutineThread, CoroutineThreadFactory
from src.saga.orchestration import ThreadedOrchestrator, CoroutinesOrchestrator
from src.saga.simple_saga import SimpleSaga
from src.sys.operation_system import OperationSystemFactory, OperationSystem, ProcessingMode
from src.saga.task import Task, SystemOperation
from src.sys.time.duration import Duration


class TestThreadedOrchestrator(TestCase):
    def test_process(self):
        # given
        processors_factory, system = given_system_factory_that_produces_mock(
            expected_processors=2,
            expected_mode=ProcessingMode.OVERLOADED_PROCESSORS
        )
        orchestrator = ThreadedOrchestrator(
            processors_number=2,
            processing_mode=ProcessingMode.OVERLOADED_PROCESSORS,
            system_factory=processors_factory
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


class TestCoroutinesOrchestrator(TestCase):
    def test_process_when_the_number_of_sagas_is_greater_then_the_number_of_processors(self):
        # given
        processors_factory, system = given_system_factory_that_produces_mock(
            expected_processors=2,
            expected_mode=ProcessingMode.FIXED_POOL_SIZE
        )
        coroutine_factory: CoroutineThreadFactory = Mock()
        orchestrator = CoroutinesOrchestrator(
            processors_number=2,
            system_factory=processors_factory,
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
                call.tick(Duration(nanos=1)),
                call.tick(Duration(nanos=1)),
                call.tick(Duration(nanos=1))
            ]
        )

    def test_process_when_the_number_of_sagas_is_lesser_then_the_number_of_processors(self):
        # given
        processors_factory, system = given_system_factory_that_produces_mock(
            expected_processors=2,
            expected_mode=ProcessingMode.FIXED_POOL_SIZE
        )
        coroutine_factory: CoroutineThreadFactory = Mock()
        orchestrator = CoroutinesOrchestrator(
            processors_number=2,
            system_factory=processors_factory,
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
                call.tick(Duration(nanos=1)),
                call.tick(Duration(nanos=1)),
                call.tick(Duration(nanos=1))
            ]
        )


def given_factory_will_return_coroutine_for(factory: CoroutineThreadFactory, sagas: [SimpleSaga]) -> CoroutineThread:
    coroutine: CoroutineThread = Mock()

    previous_factory_function = factory.new
    factory.new = lambda threads: coroutine if sagas == threads else previous_factory_function(threads)

    return coroutine


def create_task(name: str) -> Task:
    task = Task(operations=[SystemOperation(to_process=False, name=name, duration=Duration(2))])
    return task


def given_system_factory_that_produces_mock(expected_processors: int, expected_mode: ProcessingMode) -> \
        Tuple[OperationSystemFactory, OperationSystem]:
    factory = OperationSystemFactory()
    system = Mock()
    factory.create = \
        lambda processors_count, processing_mode: system \
            if processors_count == expected_processors and processing_mode == expected_mode \
            else ValueError(f"Expected {(expected_processors, expected_mode)}" +
                            f" but was {(processors_count, processing_mode)}")

    return factory, system
