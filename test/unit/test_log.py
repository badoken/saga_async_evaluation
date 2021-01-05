from typing import Any
from unittest.case import TestCase
from unittest.mock import patch, Mock

from src.log import TimeLogger, LogContext
from src.sys.time.duration import Duration
from src.sys.time.time import TimeDelta


class TestLogContext(TestCase):
    @patch("src.log.TimeLogger")
    def test_run_logging_should_provide_current_logger(self, time_logger_class):
        # given
        delta = TimeDelta(duration=Duration(seconds=2))
        logger: Mock[TimeLogger] = Mock()
        time_logger_class.return_value = logger

        # when
        actual = LogContext.run_logging(
            log_name="test",
            action=lambda: log_core_tick_and_return(core_identifier=2, to_return="expected")
        )

        # then
        logger.log_core_tick.assert_called_with(identifier=2)
        logger.close.assert_called_once()
        self.assertEqual("expected", actual)

    @patch("src.log.TimeLogger")
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

    @patch("src.log.TimeLogger")
    def test_shift_time_should_shift_time_of_logger(self, time_logger_class):
        # given
        logger: Mock[TimeLogger] = Mock()
        time_logger_class.return_value = logger

        # when
        LogContext.run_logging(
            log_name="test",
            action=lambda: LogContext.shift_time()
        )

        # then
        logger.shift_time.assert_called_with()


def log_core_tick_and_return(core_identifier: int, to_return: Any) -> Any:
    LogContext.logger().log_core_tick(identifier=core_identifier)
    return to_return
