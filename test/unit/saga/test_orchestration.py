from typing import Tuple, Callable, List
from unittest import TestCase
from unittest.mock import Mock, call, patch, ANY

from src.saga import orchestration
from src.saga.coroutine_thread import CoroutineThread, CoroutineThreadFactory
from src.saga.orchestration import ThreadedOrchestrator, CoroutinesOrchestrator
from src.saga.simple_saga import SimpleSaga
from src.saga.task import Task, SystemOperation
from src.sys.system import SystemFactory, System, ProcessingMode
from src.sys.thread import Thread
from src.sys.time.duration import Duration
from src.sys.time.time import TimeDelta


class TestRunThreads(TestCase):
    @patch("src.saga.orchestration.LogContext.shift_time")
    def test_run_threads_should_tick_system(self, shift_time_method: Callable[[], None]):
        # given
        system: Mock[System] = Mock()

        work_is_done_answers = [False for _ in range(3)]
        system.tick = Mock(side_effect=lambda duration: work_is_done_answers.pop(0))
        system.publish = Mock()

        thread: Mock[Thread] = Mock()
        system.work_is_done = lambda: next(iter(work_is_done_answers), True)
        thread.get_current_tasks = lambda: []

        # when
        result = orchestration._run_threads(threads=[thread], system=system)

        # then
        system.publish.assert_called_once_with([thread])
        system.tick.assert_has_calls(
            calls=[
                call.tick(TimeDelta(duration=Duration(micros=1), identifier=ANY)),
                call.tick(TimeDelta(duration=Duration(micros=1), identifier=ANY)),
                call.tick(TimeDelta(duration=Duration(micros=1), identifier=ANY))
            ]
        )
        self.assertEqual(Duration(micros=3), result)
        self.assertEqual(3, shift_time_method.call_count)

    @patch("src.saga.orchestration.LogContext.shift_time")
    def test_run_threads_should_call_wait_if_task_is_waiting(self, shift_time_method: Callable[[], None]):
        # given
        system: Mock[System] = Mock()

        work_is_done_answers = [False for _ in range(2)]
        system.tick = Mock(side_effect=lambda duration: work_is_done_answers.pop(0))
        system.publish = Mock()

        thread: Mock[Thread] = Mock()
        system.work_is_done = lambda: next(iter(work_is_done_answers), True)

        task_to_process: Mock[Task] = Mock()
        task_to_process.is_waiting = lambda: False
        task_to_wait: Mock[Task] = Mock()
        task_to_wait.is_waiting = lambda: True
        thread.get_current_tasks = lambda: [task_to_process, task_to_wait]

        mock_manager = Mock()
        mock_manager.attach_mock(system.tick, "tick")
        mock_manager.attach_mock(task_to_wait.wait, "wait")

        # when
        result = orchestration._run_threads(threads=[thread], system=system)

        # then
        tick1_time_delta: TimeDelta = mock_manager.tick.call_args_list[0][0][0]
        tick2_time_delta: TimeDelta = mock_manager.tick.call_args_list[1][0][0]
        wait_time_delta: TimeDelta = mock_manager.wait.call_args_list[0][1]['time_delta']

        self.assertEqual(tick1_time_delta, wait_time_delta)

        self.assertEqual(tick1_time_delta.duration, tick2_time_delta.duration)
        self.assertNotEqual(tick1_time_delta.identifier, tick2_time_delta.identifier)

        system.publish.assert_called_once_with([thread])

        self.assertEqual(Duration(micros=2), result)
        self.assertEqual(2, shift_time_method.call_count)


class TestThreadedOrchestrator(TestCase):
    @patch("src.saga.orchestration._run_threads")
    def test_process(self, run_threads_method: Callable[[List[Thread], System], Duration]):
        # given
        run_threads_method.return_value = Duration(micros=10)

        processors_factory, system = given_system_factory_that_produces_mock(
            expected_processors=2,
            expected_mode=ProcessingMode.OVERLOADED_PROCESSORS
        )
        orchestrator = ThreadedOrchestrator(
            processors_number=2,
            processing_mode=ProcessingMode.OVERLOADED_PROCESSORS,
            system_factory=processors_factory
        )

        saga: SimpleSaga = Mock()

        # when
        result = orchestrator.process(sagas=[saga])

        # then
        run_threads_method.assert_called_once_with(threads=[saga], system=system)
        self.assertEqual(Duration(micros=10), result)


class TestCoroutinesOrchestrator(TestCase):
    @patch("src.saga.orchestration._run_threads")
    def test_process_when_the_number_of_sagas_is_greater_then_the_number_of_processors(
            self,
            run_threads_method: Callable[[List[Thread], System], Duration]
    ):
        # given
        run_threads_method.return_value = Duration(micros=10)

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

        # when
        result = orchestrator.process(sagas=[saga1, saga2, saga3])

        # then
        run_threads_method.assert_called_once_with(threads=[coroutine1, coroutine2], system=system)
        self.assertEqual(Duration(micros=10), result)

    @patch("src.saga.orchestration._run_threads")
    def test_process_when_the_number_of_sagas_is_lesser_then_the_number_of_processors(
            self,
            run_threads_method: Callable[[List[Thread], System], Duration]
    ):
        # given
        run_threads_method.return_value = Duration(micros=10)

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

        coroutine = given_factory_will_return_coroutine_for(factory=coroutine_factory, sagas=[saga1])

        # when
        result = orchestrator.process(sagas=[saga1])

        # then
        run_threads_method.assert_called_once_with(threads=[coroutine], system=system)
        self.assertEqual(Duration(micros=10), result)


def given_factory_will_return_coroutine_for(factory: CoroutineThreadFactory, sagas: [SimpleSaga]) -> CoroutineThread:
    coroutine: CoroutineThread = Mock()

    previous_factory_function = factory.new
    factory.new = lambda threads: coroutine if sagas == threads else previous_factory_function(threads)

    return coroutine


def create_task(name: str) -> Task:
    task = Task(operations=[SystemOperation(to_process=False, name=name, duration=Duration(2))])
    return task


def given_system_factory_that_produces_mock(expected_processors: int, expected_mode: ProcessingMode) -> \
        Tuple[SystemFactory, System]:
    factory = SystemFactory()
    system: System = Mock()
    factory.create = \
        lambda processors_count, processing_mode: system \
            if processors_count == expected_processors and processing_mode == expected_mode \
            else None

    return factory, system
