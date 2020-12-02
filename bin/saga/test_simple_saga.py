from unittest import TestCase
from unittest.mock import Mock, PropertyMock

from bin.saga.simple_saga import SimpleSaga
from bin.sys.task import Task, SystemOperation
from bin.sys.time import Duration, TimeDelta


class TestSimpleSimpleSaga(TestCase):
    def test_tick_should_tick_all_tasks_until_they_finish(self):
        # given
        saga = SimpleSaga(tasks=[
            create_tickable_task(processing_duration_before_completion=Duration(micros=3)),
            create_tickable_task(processing_duration_before_completion=Duration(micros=2))
        ])

        # when
        saga.set_processing(True)

        # then
        self.assertFalse(saga.is_finished())

        saga.ticked(time_delta=TimeDelta(duration=Duration(micros=4)))
        self.assertFalse(saga.is_finished())

        saga.ticked(time_delta=TimeDelta(duration=Duration(micros=2)))
        self.assertTrue(saga.is_finished())

        saga.ticked(time_delta=TimeDelta(duration=Duration(micros=4)))
        self.assertTrue(saga.is_finished())

    def test_get_current_task_should_provide_first_task_if_present(self):
        # given
        task1 = create_tickable_task(processing_duration_before_completion=Duration(micros=3))
        task2 = create_tickable_task(processing_duration_before_completion=Duration(micros=2))
        saga = SimpleSaga(tasks=[task1, task2])

        # when
        result = saga.get_current_task()

        # then
        self.assertEqual(task1, result)

    def test_get_current_task_should_return_none_if_no_current_task_present(self):
        # given
        task = create_tickable_task(processing_duration_before_completion=Duration(micros=2))
        saga = SimpleSaga(tasks=[task])
        saga.set_processing(True)

        # when
        saga.ticked(time_delta=TimeDelta(duration=Duration(micros=3)))
        result = saga.get_current_task()

        # then
        self.assertIsNone(result)

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
    task.processing = PropertyMock()
    return task


def create_tickable_task(processing_duration_before_completion: Duration, to_process: bool = True) -> Task:
    task = Task(operations=[
        SystemOperation(
            to_process=to_process,
            name="task " + str(processing_duration_before_completion),
            duration=processing_duration_before_completion)
    ])

    task.ticked = Mock(wraps=task.ticked)
    return task
