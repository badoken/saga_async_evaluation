from unittest.case import TestCase
from unittest.mock import patch, Mock, call
from uuid import uuid4

from xlsxwriter import Workbook
from xlsxwriter.worksheet import Worksheet

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
        LogContext.run_logging(
            log_name="test",
            action=lambda: LogContext.logger().log_core_tick(identifier=2)
        )

        # then
        logger.log_core_tick.assert_called_with(identifier=2)
        logger.close.assert_called_once()

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


class TestTimeLogger(TestCase):
    @patch("src.log.Workbook")
    def test_log_core_should_write_each_core_in_a_separate_column(self, workbook_class):
        # given
        sheet_name = "test_name"
        workbook: Workbook = Mock()
        workbook_class.return_value = workbook

        sheet: Worksheet = Mock()
        workbook.add_worksheet = lambda name: sheet if name == sheet_name else None

        logger = TimeLogger(name=sheet_name)

        # when
        logger.log_core_tick(identifier=1)
        logger.log_core_tick(identifier=2)
        logger.shift_time()
        logger.log_core_tick(identifier=2)
        logger.close()

        # then
        sheet.write.assert_has_calls(calls=[
            call(0, 1, "core{" + str(1) + "}"),
            call(0, 2, "core{" + str(2) + "}"),

            call(1, 0, 1),
            call(1, 1, 2),
            call(1, 2, 2),

            call(2, 0, 2),
            call(2, 1, 0),
            call(2, 2, 2)
        ], any_order=True)

        workbook.close.assert_called_once()

    @patch("src.log.Workbook")
    def test_log_task_should_write_each_task_in_a_separate_column(self, workbook_class):
        # given
        first_task_id = uuid4()
        second_task_id = uuid4()

        sheet_name = "test_name"
        workbook: Workbook = Mock()
        workbook_class.return_value = workbook

        sheet: Worksheet = Mock()
        workbook.add_worksheet = lambda name: sheet if name == sheet_name else None

        logger = TimeLogger(name=sheet_name)

        # when
        logger.log_task_waiting(name="a", identifier=first_task_id)
        logger.log_task_processing(name="b", identifier=second_task_id)
        logger.shift_time()
        logger.log_task_processing(name="a", identifier=first_task_id)
        logger.close()

        # then
        sheet.write.assert_has_calls(calls=[
            call(0, 1, "t{a}[" + str(first_task_id) + "]"),
            call(0, 2, "t{b}[" + str(second_task_id) + "]"),

            call(1, 0, 1),
            call(1, 1, 1),
            call(1, 2, 2),

            call(2, 0, 2),
            call(2, 1, 2),
            call(2, 2, 0)
        ], any_order=True)

        workbook.close.assert_called_once()

    @patch("src.log.Workbook")
    def test_log_task_should_not_write_same_core_two_times(self, workbook_class):
        # given
        task_id = uuid4()

        sheet_name = "test_name"
        workbook: Workbook = Mock()
        workbook_class.return_value = workbook

        sheet: Worksheet = Mock()
        workbook.add_worksheet = lambda name: sheet if name == sheet_name else None

        logger = TimeLogger(name=sheet_name)

        logger.log_task_waiting(name="a", identifier=task_id)

        # when
        try:
            logger.log_task_processing(name="a", identifier=task_id)
        # then
        except ValueError:
            return

        self.fail("Should throw exception")
