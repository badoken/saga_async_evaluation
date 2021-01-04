from unittest.case import TestCase

from parameterized import parameterized

from src.sys.time.duration import Duration


class TestDuration(TestCase):
    def test_seconds_milliseconds_and_microseconds(self):
        # given
        duration = Duration(micros=567, millis=728, seconds=22)

        # when
        seconds = duration.seconds
        milliseconds = duration.millis
        microseconds = duration.micros

        # then
        self.assertEqual(seconds, 22.728567)
        self.assertEqual(milliseconds, 22728.567)
        self.assertEqual(microseconds, 22728567)

    def test_string_representation(self):
        # given
        duration = Duration(micros=5674, millis=3728, seconds=22)

        # when
        string = duration.__str__()
        representation = duration.__repr__()

        # then
        self.assertEqual(string, representation)
        self.assertEqual("🕒:25s733ms674μs", string)

    def test_minus_string_representation(self):
        # given
        duration = Duration(micros=5674, millis=3728, seconds=-22)

        # when
        string = duration.__str__()
        representation = duration.__repr__()

        # then
        self.assertEqual(string, representation)
        self.assertEqual("🕒:-18s266ms326μs", string)

    def test_eq(self):
        # given
        duration = Duration(micros=1)
        duration_same = Duration(micros=1)
        duration_different = Duration(micros=2)

        # when
        same_eq = duration == duration_same
        different_eq = duration == duration_different

        # then
        self.assertTrue(same_eq)
        self.assertFalse(different_eq)

    def test_rand_between_should_return_duration_in_range(self):
        # given
        start = Duration(micros=2)
        end = Duration(seconds=1)

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
            self.fail("Unexpected exception when started = " + str(start))

        if not prohibited:
            return

        self.fail("Expected an exception to be thrown when started = " + str(start))

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
