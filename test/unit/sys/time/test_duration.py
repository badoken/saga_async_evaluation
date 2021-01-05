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
