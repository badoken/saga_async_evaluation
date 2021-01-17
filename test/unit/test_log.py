from __future__ import annotations

from dataclasses import replace
from typing import Any, Callable, Set, cast
from unittest.case import TestCase
from unittest.mock import patch, Mock, ANY, call
from uuid import uuid4

from src.log import TimeLogger, LogContext, Report, Percentage, ProcessorNumber, print_coloured
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
            action=lambda: log_processor_tick_and_return(proc_number=ProcessorNumber(2), to_return="expected")
        )

        # then
        logger.log_processor_tick.assert_called_with(proc_number=2)
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


def log_processor_tick_and_return(proc_number: ProcessorNumber, to_return: Any) -> Any:
    LogContext.logger().log_processor_tick(proc_number=proc_number)
    return to_return


class TestTimeLogger(TestCase):
    def test_log_task_processing_cannot_happen_after_another_task_trigger(self):
        # given
        logger = TimeLogger(name="logger")
        logger.log_processor_tick(proc_number=3)
        log_random_task_processing(logger)

        # when
        try:
            log_random_task_processing(logger)

        # then
        except ValueError:
            return

        self.fail("Had to throw an exception")

    def test_log_overhead_tick_cannot_happen_after_another_task_trigger(self):
        # given
        logger = TimeLogger(name="logger")
        logger.log_processor_tick(proc_number=3)
        log_random_task_processing(logger)

        # when
        try:
            logger.log_overhead_tick()

        # then
        except ValueError:
            return

        self.fail("Had to throw an exception")

    def test_log_overhead_tick_cannot_happen_after_another_overhead(self):
        # given
        logger = TimeLogger(name="logger")
        logger.log_processor_tick(proc_number=3)
        logger.log_overhead_tick()

        # when
        try:
            logger.log_overhead_tick()

        # then
        except ValueError:
            return

        self.fail("Had to throw an exception")

    def test_task_trigger_should_be_able_to_happen_after_another_task_trigger_and_proc_ticked_in_between(self):
        # given
        logger = TimeLogger(name="logger")
        logger.log_processor_tick(proc_number=3)
        log_random_task_processing(logger)

        # when
        logger.shift_time()
        logger.log_processor_tick(proc_number=3)
        try:
            log_random_task_processing(logger=logger)

        # then
        except ValueError:
            self.fail("Had to throw an exception")

    def test_close_should_report_the_proc_percentages(self):
        # given
        report_publisher: Mock[Callable[[Report], None]] = Mock()
        logger = TimeLogger(name="logger", report_publisher=cast(Callable[[Report], None], report_publisher))

        # when
        logger.log_processor_tick(proc_number=5)
        log_random_task_processing(logger)
        logger.log_processor_tick(proc_number=3)
        logger.shift_time()

        logger.log_processor_tick(proc_number=3)
        logger.log_overhead_tick()
        logger.shift_time()

        logger.log_processor_tick(proc_number=3)
        log_random_task_processing(logger)
        logger.shift_time()

        logger.log_processor_tick(proc_number=3)
        log_random_task_processing(logger)

        logger.close()

        # then
        report_publisher.assert_called_once_with(
            replace(
                log_report_with_any_values(log_name="logger"),
                processor_task_handling_percentage=Percentage(75),
                processor_waiting_percentage=Percentage(12.5),
                processor_overhead_work_percentage=Percentage(12.5)
            )
        )

    def test_close_should_report_the_average_time_of_proc_processing(self):
        # given
        report_publisher: Mock[Callable[[Report], None]] = Mock()
        logger = TimeLogger(name="logger", report_publisher=cast(Callable[[Report], None], report_publisher))

        # when
        logger.log_processor_tick(proc_number=5)
        log_random_task_processing(logger)
        logger.log_processor_tick(proc_number=3)
        log_random_task_processing(logger)
        logger.shift_time()

        logger.log_processor_tick(proc_number=3)
        log_random_task_processing(logger)
        logger.shift_time()

        logger.log_processor_tick(proc_number=3)
        log_random_task_processing(logger)
        logger.shift_time()

        logger.log_processor_tick(proc_number=3)
        log_random_task_processing(logger)

        logger.close()

        # then
        report_publisher.assert_called_once_with(
            replace(
                log_report_with_any_values(log_name="logger"),
                avg_processor_task_handling=Duration(micros=2)
            )
        )

    def test_close_should_report_the_average_time_of_proc_overhead(self):
        # given
        report_publisher: Mock[Callable[[Report], None]] = Mock()
        logger = TimeLogger(name="logger", report_publisher=cast(Callable[[Report], None], report_publisher))

        # when
        logger.log_processor_tick(proc_number=5)
        logger.log_overhead_tick()
        logger.log_processor_tick(proc_number=3)
        logger.log_overhead_tick()
        logger.shift_time()

        logger.log_processor_tick(proc_number=3)
        logger.log_overhead_tick()
        logger.shift_time()

        logger.log_processor_tick(proc_number=3)
        logger.log_overhead_tick()
        logger.shift_time()

        logger.log_processor_tick(proc_number=3)
        logger.log_overhead_tick()

        logger.close()

        # then
        report_publisher.assert_called_once_with(
            replace(
                log_report_with_any_values(log_name="logger"),
                avg_processor_overhead_work=Duration(micros=2)
            )
        )

    def test_close_should_report_the_average_time_of_proc_waiting(self):
        # given
        report_publisher: Mock[Callable[[Report], None]] = Mock()
        logger = TimeLogger(name="logger", report_publisher=cast(Callable[[Report], None], report_publisher))

        # when
        logger.log_processor_tick(proc_number=5)
        logger.log_processor_tick(proc_number=3)
        logger.shift_time()

        logger.log_processor_tick(proc_number=3)
        logger.shift_time()

        logger.log_processor_tick(proc_number=3)
        logger.shift_time()

        logger.log_processor_tick(proc_number=3)

        logger.close()

        # then
        report_publisher.assert_called_once_with(
            replace(
                log_report_with_any_values(log_name="logger"),
                avg_processor_waiting=Duration(micros=2)
            )
        )

    def test_close_should_report_the_duration_of_simulation(self):
        # given
        report_publisher: Mock[Callable[[Report], None]] = Mock()
        logger = TimeLogger(name="logger", report_publisher=cast(Callable[[Report], None], report_publisher))

        # when
        logger.log_processor_tick(proc_number=5)
        log_random_task_processing(logger)
        logger.log_processor_tick(proc_number=3)
        log_random_task_processing(logger)
        logger.shift_time()

        logger.log_processor_tick(proc_number=3)
        logger.close()

        # then
        report_publisher.assert_called_once_with(
            replace(
                log_report_with_any_values(log_name="logger"),
                simulation_duration=Duration(micros=2)
            )
        )

    def test_publish_report_every_should_publish_report_each_duration_passed(self):
        # given
        report_publisher: Mock[Callable[[Report], None]] = Mock()
        logger = TimeLogger(
            name="logger",
            publish_report_every=Duration(micros=2),
            report_publisher=cast(Callable[[Report], None], report_publisher)
        )

        # when
        logger.log_processor_tick(proc_number=5)
        logger.shift_time()

        logger.log_processor_tick(proc_number=2)
        logger.shift_time()

        logger.log_processor_tick(proc_number=1)

        logger.close()

        # then
        report_publisher.assert_has_calls(calls=[
            call(replace(
                log_report_with_any_values(log_name="logger"),
                simulation_duration=Duration(micros=2)
            )),
            call(replace(
                log_report_with_any_values(log_name="logger"),
                simulation_duration=Duration(micros=3)
            ))
        ])


def log_random_task_processing(logger: TimeLogger):
    logger.log_task_processing(name=f"task{uuid4()}", identifier=uuid4())


class TestPrintColored(TestCase):
    @patch('src.log.colored')
    @patch('src.log.print')
    def test_print_coloured_should_print_a_report_with_a_different_name_in_a_different_color(self, pr, col):
        # given
        report1 = log_report_with_any_values("log1")
        report2 = log_report_with_any_values("log2")

        col.return_value = "expected"

        # when
        print_coloured(report1)
        print_coloured(report2)

        # then
        pr.assert_has_calls([call("expected"), call("expected")])
        self.assertEqual(2, len(col.call_args_list))

        already_used_colors: Set[str] = set()
        for report, params_map in col.call_args_list:
            color = params_map["color"]
            self.assertNotIn(color, already_used_colors)
            already_used_colors.add(color)

    @patch('src.log.colored')
    @patch('builtins.print')
    def test_print_colored_should_print_a_report_with_a_same_name_in_the_same_color(self, pr, col):
        # given
        report1 = log_report_with_any_values("log")
        report2 = log_report_with_any_values("log")

        col.return_value = "expected"

        # when
        print_coloured(report1)
        print_coloured(report2)

        # then
        pr.assert_has_calls([call("expected"), call("expected")])
        self.assertEqual(2, len(col.call_args_list))

        report, params_map = col.call_args_list[0]
        color = params_map["color"]
        col.assert_has_calls([call(str(report1), color=color), call(str(report2), color=color)])


def log_report_with_any_values(log_name: str):
    return Report(
        log_name=log_name,
        simulation_duration=ANY,
        avg_processor_task_handling=ANY,
        processor_task_handling_percentage=ANY,
        avg_processor_waiting=ANY,
        processor_waiting_percentage=ANY,
        avg_processor_overhead_work=ANY,
        processor_overhead_work_percentage=ANY
    )
