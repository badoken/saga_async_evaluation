from typing import List, Any
from unittest import TestCase
from unittest.mock import Mock, call, ANY

from src.log import TimeLogger, LogContext
from src.sys.thread import Thread
from src.sys.processor import Processor
from src.sys.time.time import TimeDelta
from src.sys.time.duration import Duration


class TestProcessor(TestCase):
    log_context_logger = LogContext.logger

    @classmethod
    def tearDownClass(cls):
        LogContext.logger = cls.log_context_logger

    def test_ticked_should_tick_one_thread_till_its_finished(self):
        # given
        logger = given_logging_context_that_provides_logger()

        thread = create_thread(ticks=2)
        processor = Processor(processing_interval=Duration(20))

        # when
        processor.assign(thread)
        processor.ticked(time_delta=TimeDelta(Duration(micros=1)))
        processor.ticked(time_delta=TimeDelta(Duration(micros=1)))
        processor.ticked(time_delta=TimeDelta(Duration(micros=1)))

        # then
        thread.ticked.assert_has_calls([
            call.ticked(TimeDelta(duration=Duration(micros=1), identifier=ANY)),
            call.ticked(TimeDelta(duration=Duration(micros=1), identifier=ANY))
        ])
        logger.log_processor_tick.assert_has_calls([
            call(proc_number=processor.number),
            call(proc_number=processor.number)
        ])

    def test_is_starving_should_return_true_when_all_threads_are_processed(self):
        # given
        logger = given_logging_context_that_provides_logger()

        thread1, thread2 = create_threads(count=2, ticks=1)
        processor = Processor(processing_interval=Duration(5))

        # when
        processor.assign(thread1)
        processor.assign(thread2)

        # then
        self.assertFalse(processor.is_starving())
        processor.ticked(time_delta=TimeDelta(Duration(micros=1)))
        self.assertFalse(processor.is_starving())
        processor.ticked(time_delta=TimeDelta(Duration(micros=1)))
        self.assertTrue(processor.is_starving())

        logger.log_processor_tick.assert_has_calls([
            call(proc_number=processor.number),
            call(proc_number=processor.number)
        ])

    def test_is_starving_should_return_true_when_thread_is_processed(self):
        # given
        logger = given_logging_context_that_provides_logger()

        thread1 = create_thread(ticks=1)
        processor = Processor(processing_interval=Duration(5))

        # when
        processor.assign(thread1)

        # then
        self.assertFalse(processor.is_starving())
        processor.ticked(time_delta=TimeDelta(Duration(micros=1)))
        self.assertTrue(processor.is_starving())

        logger.log_processor_tick.assert_called_once_with(proc_number=processor.number)

    def test_is_starving_should_return_false_when_new_thread_is_assigned(self):
        # given
        logger = given_logging_context_that_provides_logger()

        thread1 = create_thread(ticks=1)
        processor = Processor(processing_interval=Duration(5))
        processor.assign(thread1)

        thread2 = create_thread(ticks=1)

        # when
        processor.ticked(time_delta=TimeDelta(Duration(micros=1)))
        processor.assign(thread2)

        # then
        self.assertFalse(processor.is_starving())

        logger.log_processor_tick.assert_called_once_with(proc_number=processor.number)

    def test_is_starving_should_return_false_when_switching_context(self):
        # given
        logger = given_logging_context_that_provides_logger()

        thread1 = create_thread(ticks=20)
        thread2 = create_thread(ticks=20)
        processor = Processor(processing_interval=Duration(micros=5))
        processor.assign(thread1)
        processor.assign(thread2)

        # when
        processor.ticked(TimeDelta(Duration(micros=5)))

        # then
        for microseconds in range(processor._context_switch_cost.micros + 5):
            self.assertFalse(
                processor.is_starving(),
                msg=f"Should not be starving during context switch and after at {Duration(micros=microseconds)}"
            )
            processor.ticked(time_delta=TimeDelta(Duration(micros=1)))

        logger.log_processor_tick.assert_has_calls(
            [
                call(proc_number=processor.number)
                for _
                in range(processor._context_switch_cost.micros + 6)
            ]
        )

    def test_tick_should_not_switch_context_with_one_thread(self):
        # given
        logger = given_logging_context_that_provides_logger()

        thread = create_thread(ticks=10)
        processor = Processor(processing_interval=Duration(2))
        processor.assign(thread)

        # when
        for microsecond in range(10):
            processor.ticked(TimeDelta(Duration(micros=1)))
            processor.ticked(time_delta=TimeDelta(Duration(micros=1)))

        # then
        self.assertTrue(
            processor.is_starving(),
            msg="Should be starving after the work is done"
        )
        logger.log_processor_tick.assert_has_calls(
            [
                call(proc_number=processor.number)
                for _
                in range(10)
            ]
        )

    def test_ticked_should_switch_threads_if_processing_interval_is_not_multiple_of_context_switch_cost(self):
        # given
        logger = given_logging_context_that_provides_logger()

        thread1 = create_thread(ticks=20)
        thread2 = create_thread(ticks=20)
        processor = Processor(processing_interval=Duration(micros=6), context_switch_cost=Duration(micros=2))

        # when
        processor.assign(thread1)
        processor.assign(thread2)

        for tick_number in range(10):
            processor.ticked(time_delta=TimeDelta(Duration(micros=3)))

        # then
        self.assert_only_calls(called(times=4, duration=Duration(micros=3)), thread1.ticked)
        self.assert_only_calls(called(times=3, duration=Duration(micros=3)), thread2.ticked)
        logger.log_processor_tick.assert_has_calls(
            [
                call(proc_number=processor.number)
                for _
                in range(10)
            ]
        )

    def test_ticked_should_switch_threads_if_processing_interval_is_multiple_of_context_switch_cost(self):
        # given
        logger = given_logging_context_that_provides_logger()

        thread1 = create_thread(ticks=20)
        thread2 = create_thread(ticks=20)
        processor = Processor(processing_interval=Duration(micros=6), context_switch_cost=Duration(micros=2))

        # when
        processor.assign(thread1)
        processor.assign(thread2)

        for tick_number in range(10):
            processor.ticked(time_delta=TimeDelta(Duration(micros=4)))

        # then
        self.assert_only_calls(called(times=4, duration=Duration(micros=4)), thread1.ticked)
        self.assert_only_calls(called(times=3, duration=Duration(micros=4)), thread2.ticked)
        logger.log_processor_tick.assert_has_calls(
            [
                call(proc_number=processor.number)
                for _
                in range(10)
            ]
        )

    def assert_only_calls(self, expected_calls: List[Any], mock: Any):
        self.assertEqual(expected_calls, mock.mock_calls)


def create_threads(count: int, ticks: int) -> List[Thread]:
    return [create_thread(ticks, identifier) for identifier in range(count)]


def create_thread(ticks: int, identifier: int = 0) -> Thread:
    thread: Mock[Thread] = Mock(name=f"SysThread{identifier}")

    is_complete_answers: List[bool] = [False for _ in range(ticks)]

    thread.ticked = Mock(
        side_effect=lambda duration: is_complete_answers.pop(0) if len(is_complete_answers) != 0 else None
    )
    thread.is_finished = lambda: len(is_complete_answers) == 0

    return thread


def called(times: int, duration: Duration = Duration(micros=1)) -> List[Any]:
    return [call(TimeDelta(duration=duration, identifier=ANY)) for _ in range(times)]


def given_logging_context_that_provides_logger() -> Mock:
    logger: Mock[TimeLogger] = Mock()
    LogContext.logger = lambda: logger
    return logger