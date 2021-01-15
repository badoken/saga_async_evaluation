from unittest import TestCase
from unittest import TestCase
from unittest.mock import patch

from parameterized import parameterized

from src.sys.thread import KernelThread
from src.sys.time.duration import Duration
from src.sys.time.time import TimeDelta
from test.unit.sys.factories import create_executable


class TestKernelThread(TestCase):
    @parameterized.expand([
        [0, True],
        [1, True],
        [2, False],
        [3, True]
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
        thread_creation_cost_method.return_value = Duration(micros=2)
        thread_destruction_cost_method.return_value = Duration(micros=1)
        executable = create_executable(ticks=1)

        thread = KernelThread(executable)

        # when
        for _ in range(ticks):
            thread.ticked(time_delta=TimeDelta(Duration(micros=1)))

        # then
        self.assertEqual(expected_result, thread.is_doing_system_operation())

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
        thread_creation_cost_method.return_value = Duration(micros=1)
        thread_destruction_cost_method.return_value = Duration(micros=1)
        executable = create_executable(ticks=1)

        thread = KernelThread(executable)

        # when
        for _ in range(ticks):
            thread.ticked(time_delta=TimeDelta(Duration(micros=1)))

        # then
        self.assertEqual(expected_result, thread.is_finished())
