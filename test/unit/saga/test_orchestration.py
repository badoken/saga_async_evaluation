from typing import Tuple, Callable, List
from unittest import TestCase
from unittest.mock import Mock, call, patch

from saga import orchestration
from src.saga.coroutine_thread import CoroutineThread, CoroutineThreadFactory
from src.saga.orchestration import ThreadedOrchestrator, CoroutinesOrchestrator
from src.saga.simple_saga import SimpleSaga
from src.saga.task import Task, SystemOperation
from src.sys.operation_system import OperationSystemFactory, OperationSystem, ProcessingMode
from src.sys.thread import Thread
from src.sys.time.duration import Duration


class TestRunThreads(TestCase):
    def test_run_threads(self):
        # given
        os: Mock[OperationSystem] = Mock()

        work_is_done_answers = [False for _ in range(3)]
        os.tick = Mock(side_effect=lambda duration: work_is_done_answers.pop(0))
        os.publish = Mock()

        saga: Mock[SimpleSaga] = Mock()
        os.work_is_done = lambda: next(iter(work_is_done_answers), True)

        # when
        result = orchestration._run_threads([saga], os)

        # then
        os.publish.assert_called_once_with([saga])
        os.tick.assert_has_calls(
            calls=[
                call.tick(Duration(nanos=1)),
                call.tick(Duration(nanos=1)),
                call.tick(Duration(nanos=1))
            ]
        )

        self.assertEqual(Duration(nanos=3), result)


class TestThreadedOrchestrator(TestCase):
    @patch("src.saga.orchestration._run_threads")
    def test_process(self, run_threads_method: Callable[[List[Thread], OperationSystem], Duration]):
        # given
        run_threads_method.return_value = Duration(micros=10)

        processors_factory, os = given_os_factory_that_produces_mock(
            expected_processors=2,
            expected_mode=ProcessingMode.OVERLOADED_PROCESSORS
        )
        orchestrator = ThreadedOrchestrator(
            processors_number=2,
            processing_mode=ProcessingMode.OVERLOADED_PROCESSORS,
            os_factory=processors_factory
        )

        saga: SimpleSaga = Mock()

        # when
        result = orchestrator.process(sagas=[saga])

        # then
        run_threads_method.assert_called_once_with(sagas=[saga], os=os)
        self.assertEqual(Duration(micros=10), result)


class TestCoroutinesOrchestrator(TestCase):
    @patch("src.saga.orchestration._run_threads")
    def test_process_when_the_number_of_sagas_is_greater_then_the_number_of_processors(
            self,
            run_threads_method: Callable[[List[Thread], OperationSystem], Duration]
    ):
        # given
        run_threads_method.return_value = Duration(micros=10)

        processors_factory, os = given_os_factory_that_produces_mock(
            expected_processors=2,
            expected_mode=ProcessingMode.FIXED_POOL_SIZE
        )
        coroutine_factory: CoroutineThreadFactory = Mock()
        orchestrator = CoroutinesOrchestrator(
            processors_number=2,
            os_factory=processors_factory,
            coroutine_thread_factory=coroutine_factory
        )
        saga1: SimpleSaga = Mock()
        saga2: SimpleSaga = Mock()
        saga3: SimpleSaga = Mock()

        coroutine1 = given_factory_will_return_coroutine_for(factory=coroutine_factory, sagas=[saga1, saga2])
        coroutine2 = given_factory_will_return_coroutine_for(factory=coroutine_factory, sagas=[saga3])

        # when
        result = orchestrator.process(sagas=[saga1, saga2, saga3])

        # then
        run_threads_method.assert_called_once_with(sagas=[coroutine1, coroutine2], os=os)
        self.assertEqual(Duration(micros=10), result)

    @patch("src.saga.orchestration._run_threads")
    def test_process_when_the_number_of_sagas_is_lesser_then_the_number_of_processors(
            self,
            run_threads_method: Callable[[List[Thread], OperationSystem], Duration]
    ):
        # given
        run_threads_method.return_value = Duration(micros=10)

        processors_factory, os = given_os_factory_that_produces_mock(
            expected_processors=2,
            expected_mode=ProcessingMode.FIXED_POOL_SIZE
        )
        coroutine_factory: CoroutineThreadFactory = Mock()
        orchestrator = CoroutinesOrchestrator(
            processors_number=2,
            os_factory=processors_factory,
            coroutine_thread_factory=coroutine_factory
        )
        saga1: SimpleSaga = Mock()

        coroutine = given_factory_will_return_coroutine_for(factory=coroutine_factory, sagas=[saga1])

        # when
        result = orchestrator.process(sagas=[saga1])

        # then
        run_threads_method.assert_called_once_with(sagas=[coroutine], os=os)
        self.assertEqual(Duration(micros=10), result)


def given_factory_will_return_coroutine_for(factory: CoroutineThreadFactory, sagas: [SimpleSaga]) -> CoroutineThread:
    coroutine: CoroutineThread = Mock()

    previous_factory_function = factory.new
    factory.new = lambda threads: coroutine if sagas == threads else previous_factory_function(threads)

    return coroutine


def create_task(name: str) -> Task:
    task = Task(operations=[SystemOperation(to_process=False, name=name, duration=Duration(2))])
    return task


def given_os_factory_that_produces_mock(expected_processors: int, expected_mode: ProcessingMode) -> \
        Tuple[OperationSystemFactory, OperationSystem]:
    factory = OperationSystemFactory()
    os: OperationSystem = Mock()
    factory.create = \
        lambda processors_count, processing_mode: os \
            if processors_count == expected_processors and processing_mode == expected_mode \
            else None

    return factory, os
