from typing import List
from unittest import TestCase
from unittest.mock import Mock

from src.saga.simple_saga import SimpleSaga
from src.saga.task import Task
from src.sys.time.duration import Duration
from src.sys.time.time import TimeDelta


class TestSimpleSimpleSaga(TestCase):
    def test_tick_should_tick_all_tasks_until_they_finish(self):
        # given
        saga = SimpleSaga(tasks=[
            create_tickable_task(processing_duration_before_completion=Duration(micros=3)),
            create_tickable_task(processing_duration_before_completion=Duration(micros=2))
        ])

        # then
        self.assertFalse(saga.is_finished())

        saga.ticked(time_delta=TimeDelta(duration=Duration(micros=4)))
        self.assertFalse(saga.is_finished())

        saga.ticked(time_delta=TimeDelta(duration=Duration(micros=2)))
        self.assertTrue(saga.is_finished())

        saga.ticked(time_delta=TimeDelta(duration=Duration(micros=4)))
        self.assertTrue(saga.is_finished())

    def test_get_current_tasks_should_provide_first_task_if_present(self):
        # given
        task1 = create_tickable_task(processing_duration_before_completion=Duration(micros=3))
        task2 = create_tickable_task(processing_duration_before_completion=Duration(micros=2))
        saga = SimpleSaga(tasks=[task1, task2])

        # when
        result = saga.get_current_tasks()

        # then
        self.assertEqual([task1], result)

    def test_get_current_tasks_should_return_none_if_no_current_task_present(self):
        # given
        task = create_tickable_task(processing_duration_before_completion=Duration(micros=2))
        saga = SimpleSaga(tasks=[task])

        # when
        saga.ticked(time_delta=TimeDelta(duration=Duration(micros=3)))
        result = saga.get_current_tasks()

        # then
        self.assertEqual(0, len(result))

    def test_tick_should_tick_task_only_if_not_waiting(self):
        # given
        task = create_tickable_task(processing_duration_before_completion=Duration(micros=2), to_process=False)
        saga = SimpleSaga(tasks=[task])

        # when
        saga.ticked(time_delta=TimeDelta(duration=Duration(micros=3)))

        # then
        task.ticked.assert_not_called()


def create_fixed_task(completed: bool) -> Task:
    task: Task = Mock()
    task.is_complete = lambda: completed
    return task


def create_tickable_task(processing_duration_before_completion: Duration, to_process: bool = True) -> Task:
    task = Mock()
    is_finished_answered = [False for _ in range(processing_duration_before_completion.micros)]

    if to_process:
        task.wait = raise_error
        task.ticked = lambda time_delta: remove_times(elements=is_finished_answered, time_delta=time_delta)
        task.is_waiting = lambda: False
        task.is_complete = lambda: next(iter(is_finished_answered), True)
    else:
        task.ticked = raise_error
        task.wait = lambda time_delta: remove_times(elements=is_finished_answered, time_delta=time_delta)
        task.is_waiting = lambda: True
        task.is_complete = lambda: next(iter(is_finished_answered), True)

    task.ticked = Mock(wraps=task.ticked)
    return task


# noinspection PyUnusedLocal
def raise_error(time_delta: TimeDelta):
    raise Exception("Should not be called")


def remove_times(elements: List[bool], time_delta: TimeDelta):
    times = time_delta.duration.micros
    if len(elements) < times:
        elements.clear()
        return
    [
        elements.pop()
        for _
        in range(times)
    ]
