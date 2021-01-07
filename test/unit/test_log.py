from __future__ import annotations

from dataclasses import replace
from typing import Any, Callable
from unittest.case import TestCase
from unittest.mock import patch, Mock, ANY, call
from uuid import uuid4

from parameterized import parameterized

from src.log import TimeLogger, LogContext, Report, Percentage, CoreNumber
from src.sys.time.duration import Duration


class TestLogContext(TestCase):
    @patch("src.log.TimeLogger")
    def test_run_logging_should_provide_current_logger(self, time_logger_class):
        # given
        logger: Mock[TimeLogger] = Mock()
        time_logger_class.return_value = logger

        # when
        actual = LogContext.run_logging(
            log_name="test",
            action=lambda: log_core_tick_and_return(core_number=CoreNumber(2), to_return="expected")
        )

        # then
        logger.log_core_tick.assert_called_with(core_number=2)
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


def log_core_tick_and_return(core_number: CoreNumber, to_return: Any) -> Any:
    LogContext.logger().log_core_tick(core_number=core_number)
    return to_return


class TestTimeLogger(TestCase):
    @parameterized.expand([
        ["processing", "processing"],
        ["processing", "waiting"],
        ["waiting", "processing"],
        ["waiting", "waiting"]
    ])
    def test_task_trigger_cannot_happen_after_another_task_trigger(
            self,
            already_applied_log_action,
            log_action_to_apply

    ):
        # given
        logger = TimeLogger(name="logger")
        logger.log_core_tick(core_number=3)
        self.log_task(log_action_name=already_applied_log_action, logger=logger)

        # when
        try:
            self.log_task(log_action_name=log_action_to_apply, logger=logger)

        # then
        except ValueError:
            return

        self.fail("Had to throw an exception")

    @parameterized.expand([
        ["processing", "processing"],
        ["processing", "waiting"],
        ["waiting", "processing"],
        ["waiting", "waiting"]
    ])
    def test_task_trigger_should_be_able_to_happen_after_another_task_trigger_and_core_ticked_in_between(
            self,
            already_applied_log_action,
            log_action_to_apply

    ):
        # given
        logger = TimeLogger(name="logger")
        logger.log_core_tick(core_number=3)
        self.log_task(log_action_name=already_applied_log_action, logger=logger)

        # when
        logger.shift_time()
        logger.log_core_tick(core_number=3)
        try:
            self.log_task(log_action_name=log_action_to_apply, logger=logger)

        # then
        except ValueError:
            self.fail("Had to throw an exception")

    def test_close_should_report_the_core_percentages(self):
        # given
        report_publisher: Callable[[Report], None] = Mock()
        logger = TimeLogger(name="logger", report_publisher=report_publisher)

        # when
        logger.log_core_tick(core_number=5)
        self.log_task(log_action_name="processing", logger=logger)
        logger.log_core_tick(core_number=3)
        self.log_task(log_action_name="waiting", logger=logger)
        logger.shift_time()

        logger.log_core_tick(core_number=3)
        self.log_task(log_action_name="waiting", logger=logger)
        logger.shift_time()

        logger.log_core_tick(core_number=3)
        logger.shift_time()

        logger.log_core_tick(core_number=3)
        self.log_task(log_action_name="waiting", logger=logger)

        logger.close()

        # then
        report_publisher.assert_called_once_with(
            replace(
                log_report_with_any_values(log_name="logger"),
                core_processing_percentage=Percentage(20),
                core_waiting_percentage=Percentage(60),
                core_state_changing_percentage=Percentage(20)
            )
        )

    def test_close_should_report_the_average_time_of_core_waiting(self):
        # given
        report_publisher: Callable[[Report], None] = Mock()
        logger = TimeLogger(name="logger", report_publisher=report_publisher)

        # when
        logger.log_core_tick(core_number=5)
        self.log_task(log_action_name="waiting", logger=logger)
        logger.log_core_tick(core_number=3)
        self.log_task(log_action_name="waiting", logger=logger)
        logger.shift_time()

        logger.log_core_tick(core_number=3)
        self.log_task(log_action_name="waiting", logger=logger)
        logger.shift_time()

        logger.log_core_tick(core_number=3)
        self.log_task(log_action_name="waiting", logger=logger)
        logger.shift_time()

        logger.log_core_tick(core_number=3)
        self.log_task(log_action_name="waiting", logger=logger)

        logger.close()

        # then
        report_publisher.assert_called_once_with(
            replace(
                log_report_with_any_values(log_name="logger"),
                avg_core_waiting=Duration(nanos=2)
            )
        )

    def test_close_should_report_the_average_time_of_core_processing(self):
        # given
        report_publisher: Callable[[Report], None] = Mock()
        logger = TimeLogger(name="logger", report_publisher=report_publisher)

        # when
        logger.log_core_tick(core_number=5)
        self.log_task(log_action_name="processing", logger=logger)
        logger.log_core_tick(core_number=3)
        self.log_task(log_action_name="processing", logger=logger)
        logger.shift_time()

        logger.log_core_tick(core_number=3)
        self.log_task(log_action_name="processing", logger=logger)
        logger.shift_time()

        logger.log_core_tick(core_number=3)
        self.log_task(log_action_name="processing", logger=logger)
        logger.shift_time()

        logger.log_core_tick(core_number=3)
        self.log_task(log_action_name="processing", logger=logger)

        logger.close()

        # then
        report_publisher.assert_called_once_with(
            replace(
                log_report_with_any_values(log_name="logger"),
                avg_core_processing=Duration(nanos=2)
            )
        )

    def test_close_should_report_the_average_time_of_core_state_changing(self):
        # given
        report_publisher: Callable[[Report], None] = Mock()
        logger = TimeLogger(name="logger", report_publisher=report_publisher)

        # when
        logger.log_core_tick(core_number=5)
        logger.log_core_tick(core_number=3)
        logger.shift_time()

        logger.log_core_tick(core_number=3)
        logger.shift_time()

        logger.log_core_tick(core_number=3)
        logger.shift_time()

        logger.log_core_tick(core_number=3)

        logger.close()

        # then
        report_publisher.assert_called_once_with(
            replace(
                log_report_with_any_values(log_name="logger"),
                avg_core_state_changing=Duration(nanos=2)
            )
        )

    def test_close_should_report_the_duration_of_simulation(self):
        # given
        report_publisher: Callable[[Report], None] = Mock()
        logger = TimeLogger(name="logger", report_publisher=report_publisher)

        # when
        logger.log_core_tick(core_number=5)
        self.log_task(log_action_name="processing", logger=logger)
        logger.log_core_tick(core_number=3)
        self.log_task(log_action_name="waiting", logger=logger)
        logger.shift_time()

        logger.log_core_tick(core_number=3)
        logger.close()

        # then
        report_publisher.assert_called_once_with(
            replace(
                log_report_with_any_values(log_name="logger"),
                simulation_duration=Duration(nanos=2)
            )
        )

    def test_publish_report_every_should_publish_report_each_duration_passed(self):
        # given
        report_publisher: Callable[[Report], None] = Mock()
        logger = TimeLogger(name="logger", publish_report_every=Duration(nanos=2), report_publisher=report_publisher)

        # when
        logger.log_core_tick(core_number=5)
        logger.shift_time()

        logger.log_core_tick(core_number=2)
        logger.shift_time()

        logger.log_core_tick(core_number=1)

        logger.close()

        # then
        report_publisher.assert_has_calls(calls=[
            call(replace(
                log_report_with_any_values(log_name="logger"),
                simulation_duration=Duration(nanos=2)
            )),
            call(replace(
                log_report_with_any_values(log_name="logger"),
                simulation_duration=Duration(nanos=3)
            ))
        ])

    def log_task(self, log_action_name: str, logger: TimeLogger):
        if log_action_name == "processing":
            logger.log_task_processing(name=f"task{uuid4()}", identifier=uuid4())
        elif log_action_name == "waiting":
            logger.log_task_waiting(name=f"task1{uuid4()}", identifier=uuid4())
        else:
            self.fail("Unknown operation to apply")


def log_report_with_any_values(log_name: str):
    return Report(
        log_name=log_name,
        simulation_duration=ANY,
        avg_core_waiting=ANY,
        core_waiting_percentage=ANY,
        avg_core_processing=ANY,
        core_processing_percentage=ANY,
        avg_core_state_changing=ANY,
        core_state_changing_percentage=ANY
    )
