from typing import List
from unittest import TestCase
from unittest.mock import Mock, call, ANY

from src.saga.coroutine_thread import CoroutineThread
from src.sys.thread import Thread
from src.saga.task import Task
from src.sys.time.time import TimeDelta
from src.sys.time.duration import Duration


class TestCoroutineThread(TestCase):
    def test_init_should_throw_error_if_a_coroutine_specified_as_param(self):
        # given
        threads = [sys_thread("1"), CoroutineThread(sys_threads(1)), sys_thread("3")]

        # when
        try:
            CoroutineThread(threads)
        # then
        except ValueError:
            return

        self.fail("Should throw exception")

    def test_ticked_should_tick_one_thread_while_it_is_not_waiting(self):
        # given
        thread1, thread2 = sys_threads(2)
        given_thread_current_task_is_not_waiting(thread=thread1, not_waiting_ticks=3)

        coroutine = CoroutineThread(threads=[thread1, thread2])

        mock_manager = Mock()
        mock_manager.attach_mock(thread1.ticked, "ticked1")
        mock_manager.attach_mock(thread2.ticked, "ticked2")

        # when
        for _ in range(4):
            coroutine.ticked(time_delta=TimeDelta(Duration(micros=1)))

        # then
        mock_manager.assert_has_calls(
            calls=[
                call.ticked1(time_delta=TimeDelta(duration=Duration(micros=1), identifier=ANY)),
                call.ticked1(time_delta=TimeDelta(duration=Duration(micros=1), identifier=ANY)),
                call.ticked1(time_delta=TimeDelta(duration=Duration(micros=1), identifier=ANY)),
                call.ticked2(time_delta=TimeDelta(duration=Duration(micros=1), identifier=ANY))
            ]
        )

    def test_ticked_should_tick_none_threads_if_all_are_waiting(self):
        # given
        thread1, thread2 = sys_threads(2)
        given_thread_current_task_is_not_waiting(thread=thread1, not_waiting_ticks=0)
        given_thread_current_task_is_not_waiting(thread=thread2, not_waiting_ticks=0)

        coroutine = CoroutineThread(threads=[thread1, thread2])

        mock_manager = Mock()
        mock_manager.attach_mock(thread1.ticked, "ticked1")
        mock_manager.attach_mock(thread2.ticked, "ticked2")

        # when
        for _ in range(4):
            coroutine.ticked(time_delta=TimeDelta(Duration(micros=1)))

        # then
        call.ticked1.assert_not_called()
        call.ticked2.assert_not_called()

    def test_ticked_should_tick_one_thread_while_it_is_not_finished(self):
        # given
        thread1, thread2 = sys_threads(2)
        given_thread_current_task_is_not_finished(thread=thread1, not_finished_ticks=3)

        coroutine = CoroutineThread(threads=[thread1, thread2])

        mock_manager = Mock()
        mock_manager.attach_mock(thread1.ticked, "ticked1")
        mock_manager.attach_mock(thread2.ticked, "ticked2")

        # when
        for _ in range(4):
            coroutine.ticked(time_delta=TimeDelta(Duration(micros=1)))

        # then
        mock_manager.assert_has_calls(
            calls=[
                call.ticked1(time_delta=TimeDelta(duration=Duration(micros=1), identifier=ANY)),
                call.ticked1(time_delta=TimeDelta(duration=Duration(micros=1), identifier=ANY)),
                call.ticked1(time_delta=TimeDelta(duration=Duration(micros=1), identifier=ANY)),
                call.ticked2(time_delta=TimeDelta(duration=Duration(micros=1), identifier=ANY))
            ]
        )

    def test_ticked_should_tick_none_threads_if_all_are_finished(self):
        # given
        thread1, thread2 = sys_threads(2)
        given_thread_current_task_is_not_finished(thread=thread1, not_finished_ticks=0)

        coroutine = CoroutineThread(threads=[thread1, thread2])

        mock_manager = Mock()
        mock_manager.attach_mock(thread1.ticked, "ticked1")
        mock_manager.attach_mock(thread2.ticked, "ticked2")

        # when
        for _ in range(4):
            coroutine.ticked(time_delta=TimeDelta(Duration(micros=1)))

        # then
        call.ticked1.assert_not_called()
        call.ticked2.assert_not_called()

    def test_ticked_should_finish_when_all_threads_are_finished(self):
        # given
        thread1, thread2 = sys_threads(2)
        given_thread_current_task_is_not_finished(thread=thread1, not_finished_ticks=2)
        given_thread_current_task_is_not_finished(thread=thread2, not_finished_ticks=1)

        coroutine = CoroutineThread(threads=[thread1, thread2])

        # then
        self.assertFalse(coroutine.is_finished())

        # 1
        coroutine.ticked(time_delta=TimeDelta(Duration(micros=1)))
        self.assertFalse(coroutine.is_finished())

        # 2
        coroutine.ticked(time_delta=TimeDelta(Duration(micros=1)))
        self.assertFalse(coroutine.is_finished())

        # 3
        coroutine.ticked(time_delta=TimeDelta(Duration(micros=1)))
        self.assertTrue(coroutine.is_finished())

    def test_get_current_tasks_should_return_current_tasks_of_all_threads(self):
        # given
        thread1, thread2 = sys_threads(2)

        thread1_task: Task = Mock()
        thread1.get_current_tasks = lambda: [thread1_task]

        thread2_task: Task = Mock()
        thread2.get_current_tasks = lambda: [thread2_task]

        coroutine = CoroutineThread(threads=[thread1, thread2])

        # when
        actual = coroutine.get_current_tasks()

        # then
        self.assertEqual([thread1_task, thread2_task], actual)


def sys_threads(count: int) -> List[Thread]:
    return [sys_thread(name=f"thread {i + 1}") for i in range(count)]


def sys_thread(name: str = "thread") -> Thread:
    thread: Thread = Mock(name=name)
    thread.is_finished = lambda: False

    task: Task = Mock()
    task.is_waiting = lambda: False
    thread.get_current_tasks = lambda: [task]
    return thread


def given_thread_current_task_is_not_waiting(thread: Thread, not_waiting_ticks: int):
    is_waiting_answers = [False for _ in range(not_waiting_ticks)]
    current_task: Task = Mock()
    thread.get_current_tasks = lambda: [current_task]
    thread.ticked = Mock(side_effect=lambda time_delta: is_waiting_answers.pop() if is_waiting_answers else None)
    current_task.is_waiting = lambda: next(iter(is_waiting_answers), True)


def given_thread_current_task_is_not_finished(thread: Thread, not_finished_ticks: int):
    is_finished_answered = [False for _ in range(not_finished_ticks)]
    thread.ticked = Mock(side_effect=lambda time_delta: is_finished_answered.pop() if is_finished_answered else None)
    thread.is_finished = lambda: next(iter(is_finished_answered), True)
