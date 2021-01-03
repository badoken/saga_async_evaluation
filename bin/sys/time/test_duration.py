from unittest.case import TestCase

from bin.sys.time.duration import Duration


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