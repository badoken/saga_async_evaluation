from __future__ import annotations
from unittest import TestCase
from unittest.mock import patch, Mock, call

from parameterized import parameterized

from src.log import TimeLogger, LogContext
from src.sys.thread import KernelThread
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
    @patch("src.sys.thread.thread_destruction_cost")
    @patch("src.sys.thread.thread_creation_cost")
    def test_is_doing_system_operation_should_return_true_during_initialisation_and_destruction(
            self,
            ticks: int,
            expected_result: bool,
            thread_creation_cost_method,
            thread_destruction_cost_method,
    ):
        # given
        given_logging_context_that_provides_logger()

        thread_creation_cost_method.return_value = Duration(micros=2)
        thread_destruction_cost_method.return_value = Duration(micros=1)
        executable = create_executable(ticks=1)

        thread = KernelThread(executable)

        # when
        for _ in range(ticks):
            thread.ticked(time_delta=TimeDelta(Duration(micros=1)))

        # then
        self.assertEqual(expected_result, thread.is_doing_system_operation())

    @patch("src.sys.thread.thread_destruction_cost")
    @patch("src.sys.thread.thread_creation_cost")
    def test_ticked_should_tick_logging_unless_executing(
            self,
            thread_creation_cost_method,
            thread_destruction_cost_method,
    ):
        # given
        logger = given_logging_context_that_provides_logger()

        thread_creation_cost_method.return_value = Duration(micros=2)
        thread_destruction_cost_method.return_value = Duration(micros=1)
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
    @patch("src.sys.thread.thread_destruction_cost")
    @patch("src.sys.thread.thread_creation_cost")
    def test_is_finished_should_return_true_only_after_destruction(
            self,
            ticks: int,
            expected_result: bool,
            thread_creation_cost_method,
            thread_destruction_cost_method,
    ):
        # given
        given_logging_context_that_provides_logger()

        thread_creation_cost_method.return_value = Duration(micros=1)
        thread_destruction_cost_method.return_value = Duration(micros=1)
        executable = create_executable(ticks=1)

        thread = KernelThread(executable)

        # when
        for _ in range(ticks):
            thread.ticked(time_delta=TimeDelta(Duration(micros=1)))

        # then
        self.assertEqual(expected_result, thread.is_finished())


def given_logging_context_that_provides_logger() -> Mock[TimeLogger]:
    logger: Mock[TimeLogger] = Mock()
    LogContext.logger = lambda: logger
    return logger
