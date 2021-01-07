from typing import Any, List
from unittest.case import TestCase

from parameterized import parameterized

from src.sys.time.duration import Duration


class TestDuration(TestCase):
    def test_particular_values_without_surplus(self):
        # given
        duration = Duration(nanos=338, micros=567, millis=728, seconds=22)

        # when
        seconds = duration.seconds
        milliseconds = duration.millis
        microseconds = duration.micros
        nanoseconds = duration.nanos

        # then
        self.assertEqual(seconds, 22.728567338)
        self.assertEqual(milliseconds, 22728.567338)
        self.assertEqual(microseconds, 22728567.338)
        self.assertEqual(nanoseconds, 22728567338)

    def test_particular_values_without_surplus(self):
        # given
        duration = Duration(nanos=3482, micros=15888, millis=2113, seconds=5)

        # when
        seconds = duration.seconds
        milliseconds = duration.millis
        microseconds = duration.micros
        nanoseconds = duration.nanos

        # then
        self.assertEqual(seconds, 7.128891482)
        self.assertEqual(milliseconds, 7128.891482)
        self.assertEqual(microseconds, 7128891.482)
        self.assertEqual(nanoseconds, 7128891482)

    def test_string_representation(self):
        # given
        duration = Duration(nanos=665, micros=5674, millis=3728, seconds=22)

        # when
        string = duration.__str__()
        representation = duration.__repr__()

        # then
        self.assertEqual(string, representation)
        self.assertEqual("🕒:25s733ms674μs665ns", string)

    def test_minus_string_representation(self):
        # given
        duration = Duration(nanos=143, micros=5674, millis=3728, seconds=-22)

        # when
        string = duration.__str__()
        representation = duration.__repr__()

        # then
        self.assertEqual(string, representation)
        self.assertEqual("🕒:-18s266ms325μs857ns", string)

    def test_eq(self):
        # given
        duration = Duration(nanos=1)
        duration_same = Duration(nanos=1)
        duration_different = Duration(nanos=2)

        # when
        same_eq = duration == duration_same
        different_eq = duration == duration_different

        # then
        self.assertTrue(same_eq)
        self.assertFalse(different_eq)

    def test_rand_between_should_return_duration_in_range(self):
        # given
        start = Duration(micros=2)
        end = Duration(millis=1)

        # when
        actual = Duration.rand_between(start=start, end=end)

        # then
        self.assertLessEqual(start.micros, actual.micros)
        self.assertGreater(end.micros, actual.micros)

    @parameterized.expand([
        [-2, True],
        [-1, True],
        [0, False],
    ])
    def test_rand_between_should_prohibit_negative_start_value(
            self,
            start,
            prohibited
    ):
        # given
        start = Duration(micros=start)
        end = Duration(seconds=1)

        # when
        try:
            Duration.rand_between(start=start, end=end)

        # then
        except ValueError:
            if prohibited:
                return
            self.fail(f"Unexpected exception when started = {start}")

        if not prohibited:
            return

        self.fail(f"Expected an exception to be thrown when started = {start}")

    @parameterized.expand([
        [30, 21],
        [30, 30]
    ])
    def test_rand_between_should_prohibit_end_less_or_equal_to_start(
            self,
            start,
            end
    ):
        # given
        start = Duration(micros=start)
        end = Duration(micros=end)

        # when
        try:
            Duration.rand_between(start=start, end=end)

        # then
        except ValueError:
            return
        self.fail()

    @parameterized.expand([
        [Duration(nanos=6), 3, Duration(nanos=2)],
        [Duration(nanos=22), 5.5, Duration(nanos=4)],
        [Duration(nanos=15), Duration(nanos=5), Duration(nanos=3)]
    ])
    def test_truediv_should_return_quotient_if_number_specified(
            self,
            dividend: Duration,
            divisor: Any,
            quotient: Duration
    ):
        # when
        actual = dividend / divisor

        # then
        self.assertEquals(quotient, actual)

    @parameterized.expand([
        [Duration(nanos=5), Duration(nanos=15), Duration(nanos=5)],
        [Duration(nanos=25), Duration(nanos=15), Duration(nanos=10)]
    ])
    def test_mod_should_provide_quotient(
            self,
            dividend: Duration,
            divisor: Any,
            quotient: Duration
    ):
        # when
        actual = dividend % divisor

        # then
        self.assertEquals(quotient, actual)

    @parameterized.expand([
        [[Duration(nanos=5), Duration(nanos=15)], Duration(nanos=20)],
        [[Duration(nanos=25), Duration(nanos=-15)], Duration(nanos=10)],
        [[], Duration.zero()]
    ])
    def test_sum_should_return_reduction_of_all_values(
            self,
            values: List[Duration],
            expected: Any
    ):
        # when
        actual = Duration.sum(values)

        # then
        self.assertEquals(expected, actual)

    @parameterized.expand([
        [[Duration(nanos=5), Duration(nanos=15)], Duration(nanos=10)],
        [[Duration(nanos=25), Duration(nanos=-25)], Duration.zero()],
        [[], Duration.zero()]
    ])
    def test_avg_should_return_reduction_of_all_values(
            self,
            values: List[Duration],
            expected: Any
    ):
        # when
        actual = Duration.avg(values)

        # then
        self.assertEquals(expected, actual)
