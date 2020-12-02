from typing import List, Any, Callable
from unittest import TestCase
from unittest.mock import Mock, call, ANY

from bin.sys.sys_thread import SysThread
from bin.sys.core import Core
from bin.sys.time import Duration, TimeDelta


class TestCore(TestCase):
    def test_ticked_should_tick_one_thread_till_its_finished(self):
        # given
        thread = create_thread(ticks=2)
        core = Core(processing_interval=Duration(20))

        mock_manager = Mock()
        mock_manager.attach_mock(thread.set_processing, "set_processing")
        mock_manager.attach_mock(thread.ticked, "ticked")

        # when
        core.assign(thread)
        core.ticked(time_delta=TimeDelta(Duration(micros=1)))
        core.ticked(time_delta=TimeDelta(Duration(micros=1)))
        core.ticked(time_delta=TimeDelta(Duration(micros=1)))

        # then
        mock_manager.assert_has_calls(
            calls=[
                call.set_processing(True),
                call.ticked(TimeDelta(duration=Duration(micros=1), identifier=ANY)),
                call.ticked(TimeDelta(duration=Duration(micros=1), identifier=ANY)),
                call.set_processing(False)
            ]
        )

    def test_is_starving_should_return_true_when_all_threads_are_processed(self):
        # given
        thread1, thread2 = create_threads(count=2, ticks=1)
        core = Core(processing_interval=Duration(5))

        # when
        core.assign(thread1)
        core.assign(thread2)

        # then
        self.assertFalse(core.is_starving())
        core.ticked(time_delta=TimeDelta(Duration(micros=1)))
        self.assertFalse(core.is_starving())
        core.ticked(time_delta=TimeDelta(Duration(micros=1)))
        self.assertTrue(core.is_starving())

    def test_is_starving_should_return_true_when_thread_is_processed(self):
        # given
        thread1 = create_thread(ticks=1)
        core = Core(processing_interval=Duration(5))

        # when
        core.assign(thread1)

        # then
        self.assertFalse(core.is_starving())
        core.ticked(time_delta=TimeDelta(Duration(micros=1)))
        self.assertTrue(core.is_starving())

    def test_is_starving_should_return_false_when_new_thread_is_assigned(self):
        # given
        thread1 = create_thread(ticks=1)
        core = Core(processing_interval=Duration(5))
        core.assign(thread1)

        thread2 = create_thread(ticks=1)

        # when
        core.ticked(time_delta=TimeDelta(Duration(micros=1)))
        core.assign(thread2)

        # then
        self.assertFalse(core.is_starving())

    def test_is_starving_should_return_false_when_switching_context(self):
        # given
        thread1 = create_thread(ticks=20)
        thread2 = create_thread(ticks=20)
        core = Core(processing_interval=Duration(5))
        core.assign(thread1)
        core.assign(thread2)

        # when
        core.ticked(TimeDelta(Duration(micros=5)))

        # then
        for microsecond in range(core._context_switch_cost.micros + 5):
            self.assertFalse(
                core.is_starving(),
                msg="Should not be starving during context switch and after at " + str(Duration(micros=microsecond))
            )
            core.ticked(time_delta=TimeDelta(Duration(micros=1)))

    def test_tick_should_not_switch_context_with_one_thread(self):
        # given
        thread = create_thread(ticks=10)
        core = Core(processing_interval=Duration(2))
        core.assign(thread)

        # when
        for microsecond in range(10):
            core.ticked(TimeDelta(Duration(micros=1)))
            core.ticked(time_delta=TimeDelta(Duration(micros=1)))

        # then
        self.assertTrue(
            core.is_starving(),
            msg="Should be starving after the work is done"
        )

    def test_ticked_should_switch_threads_if_processing_interval_is_not_multiple_of_context_switch_cost(self):
        # given
        thread1 = create_thread(ticks=20)
        thread2 = create_thread(ticks=20)
        core = Core(processing_interval=Duration(micros=6))

        # when
        core.assign(thread1)
        core.assign(thread2)

        for tick_number in range(10):
            core.ticked(time_delta=TimeDelta(Duration(micros=3)))

        # then
        self.assert_only_calls(called(times=4, duration=Duration(micros=3)), thread1.ticked)
        self.assert_only_calls(called(times=3, duration=Duration(micros=3)), thread2.ticked)

    def test_ticked_should_switch_threads_if_processing_interval_is_multiple_of_context_switch_cost(self):
        # given
        thread1 = create_thread(ticks=20)
        thread2 = create_thread(ticks=20)
        core = Core(processing_interval=Duration(micros=6))

        # when
        core.assign(thread1)
        core.assign(thread2)

        for tick_number in range(10):
            core.ticked(time_delta=TimeDelta(Duration(micros=4)))

        # then
        self.assert_only_calls(called(times=4, duration=Duration(micros=4)), thread1.ticked)
        self.assert_only_calls(called(times=3, duration=Duration(micros=4)), thread2.ticked)

    def assert_only_calls(self, expected_calls: List[Any], mock: Any):
        self.assertEqual(expected_calls, mock.mock_calls)


def create_threads(count: int, ticks: int) -> List[SysThread]:
    return [create_thread(ticks, identifier) for identifier in range(count)]


def create_thread(ticks: int, identifier: int = 0) -> SysThread:
    thread: Mock[SysThread] = Mock(name="SysThread" + str(identifier))

    is_complete_answers: List[bool] = [False for _ in range(ticks)]

    thread.ticked = Mock(
        side_effect=lambda duration: is_complete_answers.pop(0) if len(is_complete_answers) != 0 else None
    )
    thread.is_finished = lambda: len(is_complete_answers) == 0

    return thread


def called(times: int, duration: Duration = Duration(micros=1)) -> List[Any]:
    return [call(TimeDelta(duration=duration, identifier=ANY)) for _ in range(times)]
