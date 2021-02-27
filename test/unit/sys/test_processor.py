from __future__ import annotations

from typing import List, Any
from unittest import TestCase
from unittest.mock import Mock, call, ANY

from src.log import TimeLogger, LogContext
from src.sys.processor import Processor
from src.sys.time.duration import Duration
from src.sys.time.time import TimeDelta
from src.sys.thread import KernelThread


class TestProcessor(TestCase):
    log_context_logger = LogContext.logger

    @classmethod
    def tearDownClass(cls):
        LogContext.logger = cls.log_context_logger

    def test_ticked_should_tick_one_thread_till_its_finished(self):
        # given
        logger = given_logging_context_that_provides_logger()

        thread1, thread2 = create_threads(number_of_threads=2, init_ticks=2, exec_ticks=1, wait_ticks=1, destr_ticks=2)
        processor = Processor(processing_interval=Duration(20), yielding=False)

        # when
        processor.assign(thread1)
        processor.assign(thread2)
        for _ in range(6):
            processor.ticked(time_delta=TimeDelta(Duration(micros=1)))

        # then
        self.assert_only_calls(called(times=6, duration=Duration(micros=1)), mock=thread1.ticked)
        self.assert_only_calls(called(times=0, duration=Duration(micros=1)), mock=thread2.ticked)

        logger.log_processor_tick.assert_has_calls([
            call(proc_number=processor.number)
            for _ in range(6)
        ])

    def test_is_starving_should_return_true_when_all_threads_are_processed(self):
        # given
        logger = given_logging_context_that_provides_logger()

        thread1, thread2 = create_threads(number_of_threads=2, init_ticks=3, exec_ticks=2, wait_ticks=1, destr_ticks=3)
        processor = Processor(processing_interval=Duration(2), context_switch_cost=Duration(1), yielding=False)

        # when
        processor.assign(thread1)
        processor.assign(thread2)

        # then
        # should have only 1 switch for every thread since init and destr doesn't count
        for i in range(21):
            self.assertFalse(processor.is_starving(), msg=f"Tick {i}")
            processor.ticked(time_delta=TimeDelta(Duration(micros=1)))

        self.assertFalse(processor.is_starving())

        logger.log_processor_tick.assert_has_calls([call(proc_number=processor.number) for _ in range(21)])
        logger.log_overhead_tick.assert_has_calls([call() for _ in range(4)])

    def test_tick_should_yield_control_to_another_thread_if_current_thread_can_yield(self):
        # given
        logger = given_logging_context_that_provides_logger()

        thread1, thread2 = create_threads(number_of_threads=2, init_ticks=3, exec_ticks=2, wait_ticks=1, destr_ticks=3)
        processor = Processor(context_switch_cost=Duration(2), processing_interval=Duration(20), yielding=True)

        # when
        processor.assign(thread1)
        processor.assign(thread2)
        for _ in range(10):
            processor.ticked(time_delta=TimeDelta(Duration(micros=1)))

        # then
        self.assert_only_calls(called(times=5, duration=Duration(micros=1)), mock=thread1.ticked)
        self.assert_only_calls(called(times=2, duration=Duration(micros=1)), mock=thread2.ticked)

        logger.log_processor_tick.assert_has_calls([call(proc_number=processor.number) for _ in range(8)])
        logger.log_overhead_tick.assert_has_calls([call() for _ in range(2)])

    def test_is_starving_should_return_true_when_thread_is_processed(self):
        # given
        logger = given_logging_context_that_provides_logger()

        thread = create_thread(init_ticks=1, exec_ticks=1, destr_ticks=1)
        processor = Processor(processing_interval=Duration(5), yielding=False)

        # when
        processor.assign(thread)

        # then
        for i in range(3):
            self.assertFalse(processor.is_starving(), msg=f"Tick {i}")
            processor.ticked(time_delta=TimeDelta(Duration(micros=1)))

        self.assertTrue(processor.is_starving())

        logger.log_processor_tick.assert_has_calls([call(proc_number=processor.number) for _ in range(3)])

    def test_is_starving_should_return_false_when_new_thread_is_assigned(self):
        # given
        given_logging_context_that_provides_logger()

        thread1 = create_thread(init_ticks=1, exec_ticks=1, destr_ticks=1)
        processor = Processor(processing_interval=Duration(5), yielding=False)
        processor.assign(thread1)

        thread2 = create_thread(init_ticks=1, exec_ticks=1, destr_ticks=1)

        # when
        for i in range(3):
            self.assertFalse(processor.is_starving(), msg=f"Tick {i}")
            processor.ticked(time_delta=TimeDelta(Duration(micros=1)))

        processor.assign(thread2)

        # then
        self.assertFalse(processor.is_starving())

    def test_tick_should_not_switch_context_with_one_thread(self):
        # given
        logger = given_logging_context_that_provides_logger()

        thread = create_thread(init_ticks=3, exec_ticks=4, destr_ticks=3)
        processor = Processor(processing_interval=Duration(2), yielding=False)
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
        logger.log_processor_tick.assert_has_calls([call(proc_number=processor.number) for _ in range(10)])

    def assert_only_calls(self, expected_calls: List[Any], mock: Any):
        self.assertEqual(expected_calls, mock.mock_calls)


def called(times: int, duration: Duration = Duration(micros=1)) -> List[Any]:
    return [call(TimeDelta(duration=duration, identifier=ANY)) for _ in range(times)]


def given_logging_context_that_provides_logger() -> Mock[TimeLogger]:
    logger: Mock[TimeLogger] = Mock()
    LogContext.logger = lambda: logger
    return logger


def create_threads(
        number_of_threads: int,
        init_ticks: int,
        exec_ticks: int,
        destr_ticks: int,
        wait_ticks: int = 0
) -> List[Mock[KernelThread]]:
    return [create_thread(init_ticks, exec_ticks, destr_ticks, wait_ticks) for _ in range(number_of_threads)]


def create_thread(init_ticks: int, exec_ticks: int, destr_ticks: int, wait_ticks: int = 0) -> Mock[KernelThread]:
    thread: Mock[KernelThread] = Mock()
    thread.tick_scenario: List[str] = []
    for _ in range(init_ticks):
        thread.tick_scenario.append("init")
    for _ in range(exec_ticks):
        thread.tick_scenario.append("exec")
    for _ in range(wait_ticks):
        thread.tick_scenario.append("wait")
    for _ in range(destr_ticks):
        thread.tick_scenario.append("destr")
    thread.ticked = Mock()
    thread.ticked.side_effect = lambda time_delta: [
        thread.tick_scenario.pop(0) if thread.tick_scenario else None
        for _
        in range(time_delta.duration.micros)
    ]
    thread.is_doing_system_operation = lambda: next(iter(thread.tick_scenario), False) in ("init", "destr")
    thread.can_yield = lambda: next(iter(thread.tick_scenario), False) == "wait"
    thread.is_finished = lambda: len(thread.tick_scenario) == 0
    return thread
