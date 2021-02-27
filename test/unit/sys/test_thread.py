from __future__ import annotations
from unittest import TestCase
from unittest.mock import patch, Mock, call

from parameterized import parameterized

from src.log import TimeLogger, LogContext
from src.saga.task import Task
from src.sys.thread import KernelThread, ChainOfExecutables
from src.sys.time.duration import Duration
from src.sys.time.time import TimeDelta
from test.unit.sys.factories import create_executable


class TestKernelThread(TestCase):
    log_context_logger = LogContext.logger

    @classmethod
    def tearDownClass(cls):
        LogContext.logger = cls.log_context_logger

    @parameterized.expand([
        [0, True],
        [1, True],
        [2, False],
        [3, True],
        [4, False]
    ])
    @patch("src.sys.thread.thread_deallocation_cost")
    @patch("src.sys.thread.thread_creation_cost")
    def test_is_doing_system_operation_should_return_true_during_initialisation_and_destruction(
            self,
            ticks: int,
            expected_result: bool,
            thread_creation_cost_method,
            thread_deallocation_cost_method,
    ):
        # given
        given_logging_context_that_provides_logger()

        thread_creation_cost_method.return_value = Duration(micros=2)
        thread_deallocation_cost_method.return_value = Duration(micros=1)
        executable = create_executable(ticks=1)

        thread = KernelThread(executable)

        # when
        for _ in range(ticks):
            thread.ticked(time_delta=TimeDelta(Duration(micros=1)))

        # then
        self.assertEqual(expected_result, thread.is_doing_system_operation())

    @patch("src.sys.thread.thread_deallocation_cost")
    @patch("src.sys.thread.thread_creation_cost")
    def test_ticked_should_tick_logging_unless_executing(
            self,
            thread_creation_cost_method,
            thread_deallocation_cost_method,
    ):
        # given
        logger = given_logging_context_that_provides_logger()

        thread_creation_cost_method.return_value = Duration(micros=2)
        thread_deallocation_cost_method.return_value = Duration(micros=1)
        executable = create_executable(ticks=1)

        thread = KernelThread(executable)

        # when
        for _ in range(5):
            thread.ticked(time_delta=TimeDelta(Duration(micros=1)))

        # then
        logger.log_overhead_tick.assert_has_calls([call() for _ in range(3)])

    @parameterized.expand([
        [0, False],
        [1, False],
        [2, False],
        [3, True],
        [4, True]
    ])
    @patch("src.sys.thread.thread_deallocation_cost")
    @patch("src.sys.thread.thread_creation_cost")
    def test_is_finished_should_return_true_only_after_destruction(
            self,
            ticks: int,
            expected_result: bool,
            thread_creation_cost_method,
            thread_deallocation_cost_method,
    ):
        # given
        given_logging_context_that_provides_logger()

        thread_creation_cost_method.return_value = Duration(micros=1)
        thread_deallocation_cost_method.return_value = Duration(micros=1)
        executable = create_executable(ticks=1)

        thread = KernelThread(executable)

        # when
        for _ in range(ticks):
            thread.ticked(time_delta=TimeDelta(Duration(micros=1)))

        # then
        self.assertEqual(expected_result, thread.is_finished())

    @parameterized.expand([
        [0, False],
        [1, False],
        [2, True],
        [3, False],
        [4, False]
    ])
    @patch("src.sys.thread.thread_deallocation_cost")
    @patch("src.sys.thread.thread_creation_cost")
    def test_can_yield_should_return_true_only_if_current_task_is_waiting(
            self,
            ticks: int,
            expected_result: bool,
            thread_creation_cost_method,
            thread_deallocation_cost_method,
    ):
        # given
        given_logging_context_that_provides_logger()

        thread_creation_cost_method.return_value = Duration(micros=1)
        thread_deallocation_cost_method.return_value = Duration(micros=1)
        executable = create_executable(ticks=1, waits=1)

        thread = KernelThread(executable)

        # when
        for _ in range(ticks):
            thread.ticked(time_delta=TimeDelta(Duration(micros=1)))

        # then
        self.assertEqual(expected_result, thread.can_yield())


class TestChainOfExecutables(TestCase):
    def test_is_finished_should_return_false_until_all_executables_are_finished(self):
        # given
        ex1 = create_executable(ticks=2, identifier=1)
        ex2 = create_executable(ticks=3, identifier=2)

        # when
        chain = ChainOfExecutables(ex1, ex2)

        # then
        self.assertFalse(chain.is_finished())

        for i in range(4):
            chain.ticked(TimeDelta(Duration(micros=1)))
            self.assertFalse(chain.is_finished(), msg=f"had to be not finished after {i + 1} ticks")

        chain.ticked(TimeDelta(Duration(micros=1)))
        self.assertTrue(chain.is_finished(), msg=f"had to be not finished after 5 ticks")

    def test_is_finished_should_return_true_if_no_executables_specified(self):
        # when
        chain = ChainOfExecutables()

        # then
        self.assertTrue(chain.is_finished())

    def test_get_current_tasks_should_return_current_task_of_a_current_executable(self):
        # given
        ex1 = create_executable(ticks=2, identifier=1)
        ex2 = create_executable(ticks=3, identifier=2)

        expectedTask: Task = Mock()
        ex2.get_current_tasks = lambda: [expectedTask]

        chain = ChainOfExecutables(ex1, ex2)

        for i in range(2):
            chain.ticked(TimeDelta(Duration(micros=1)))

        # when
        actualTasks = chain.get_current_tasks()

        # then
        self.assertEqual([expectedTask], actualTasks)


def given_logging_context_that_provides_logger() -> Mock[TimeLogger]:
    logger: Mock[TimeLogger] = Mock()
    LogContext.logger = lambda: logger
    return logger
