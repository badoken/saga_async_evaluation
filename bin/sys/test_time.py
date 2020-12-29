from typing import Type
from unittest import TestCase
from unittest.mock import patch, Mock

from bin.sys.time import Duration, TimeDelta, TimeLogger, LogContext


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


class TestTimeDelta(TestCase):
    def test_new_instance_should_be_unique(self):
        # given
        first = TimeDelta(duration=Duration(micros=1))
        second = TimeDelta(duration=Duration(micros=1))

        # when
        equals = first.__eq__(second)

        # then
        self.assertFalse(equals)

    def test_new_instance_should_have_unique_identifier(self):
        # given
        first = TimeDelta(duration=Duration(micros=1))
        second = TimeDelta(duration=Duration(micros=1))

        # when
        first_id = first.identifier
        second_id = second.identifier

        # then
        self.assertNotEqual(first_id, second_id)


class TestLogContext(TestCase):
    @patch("bin.sys.time.TimeLogger")
    def test_run_logging_should_provide_current_logger(self, time_logger_class):
        # given
        delta = TimeDelta(duration=Duration(seconds=2))
        logger: Mock[TimeLogger] = Mock()
        time_logger_class.return_value = logger

        # when
        LogContext.run_logging(
            log_name="test",
            action=lambda: LogContext.logger().log_core_tick(time_delta=delta, identifier=2)
        )

        # then
        logger.log_core_tick.assert_called_with(time_delta=delta, identifier=2)
        logger.close.assert_called_once()

    @patch("bin.sys.time.TimeLogger")
    def test_logger_is_inaccessible_outside_of_context(self, time_logger_class):
        # given
        logger: Mock[TimeLogger] = Mock()
        time_logger_class.return_value = logger

        # when
        actual_logger = LogContext.logger()

        # then
        self.assertIsNone(actual_logger)

        logger.assert_not_called()
        logger.close.assert_not_called()
