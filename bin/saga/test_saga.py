from unittest import TestCase
from unittest.mock import Mock

from bin.saga.saga import Saga
from bin.sys.task import Task, SystemOperation
from bin.sys.time import TimeUnit


class TestSaga(TestCase):
    def test_is_finished_should_return_false_if_one_of_tasks_is_not_finished(self):
        for tasks in [
            [create_task(completed=True), create_task(completed=False)],
            [create_task(completed=False), create_task(completed=True)],
            [create_task(completed=False), create_task(completed=False)]
        ]:
            # given
            saga = Saga(tasks)

            # when
            finished = saga.is_finished()

            # then
            self.assertFalse(finished)

    def test_is_finished_should_return_true_if_all_tasks_are_finished(self):
        # given
        saga = Saga(tasks=[create_task(completed=True), create_task(completed=True)])

        # when
        finished = saga.is_finished()

        # then
        self.assertTrue(finished)

    def test_next_incomplete_task_should_return_latest_incomplete(self):
        for expected, tasks in [
            (
                    create_task(completed=False, name="expected"),
                    [create_task(completed=True, name="finished"), create_task(completed=False, name="expected")]
            ),
            (
                    create_task(completed=False, name="expected"),
                    [create_task(completed=False, name="expected"), create_task(completed=False, name="not started")]
            ),
            (
                    None,
                    [create_task(completed=True, name="finished1"), create_task(completed=True, name="finished2")]
            )
        ]:
            # given
            saga = Saga(tasks)

            # when
            incomplete = saga.last_incomplete_task()

            # then
            self.assertEqual(incomplete, expected)


def create_task(completed: bool, name: str = "name") -> Task:
    task = Task(operations=[SystemOperation(to_process=True, name=name, duration=TimeUnit(2))])
    task.is_complete = lambda: completed
    return task
