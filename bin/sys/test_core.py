from unittest import TestCase

from bin.sys.time import TimeUnit
from bin.sys.task import Task, SystemOperation
from bin.sys.core import Core, Mode


class TestCore(TestCase):
    def test_ticked_should_assign_core_to_the_first_task(self):
        # given
        task1 = Task(operations=[SystemOperation(to_process=True, name="1", duration=TimeUnit(2))])
        task2 = Task(operations=[SystemOperation(to_process=False, name="2", duration=TimeUnit(1))])
        pool = [task1, task2]

        Core(unassigned_tasks_pool=pool, mode=Mode.SYNC)
        core2 = Core(unassigned_tasks_pool=pool, mode=Mode.ASYNC)

        # when
        core2.ticked()

        # then
        self.assertEqual([task2], pool)
        self.assertEqual(task1, core2._processing)

    def test_ticked_should_stick_sync_core_with_task_until_its_finished(self):
        for to_process in [True, False]:
            # given
            task = Task(operations=[SystemOperation(to_process=to_process, name="1", duration=TimeUnit(2))])
            pool = [task]

            core = Core(unassigned_tasks_pool=pool, mode=Mode.SYNC)

            # then
            core.ticked()
            self.assertEqual([], pool)
            self.assertEqual(task, core._processing)

            core.ticked()
            self.assertEqual([], pool)
            self.assertEqual(None, core._processing)

    def test_ticked_should_stick_core_with_task_until_its_part_finished_and_return_task_to_the_pool(self):
        # given
        task = Task(operations=[
            SystemOperation(to_process=True, name="action", duration=TimeUnit(2)),
            SystemOperation(to_process=False, name="wait", duration=TimeUnit(2))
        ])
        pool = [task]

        core = Core(unassigned_tasks_pool=pool, mode=Mode.ASYNC)

        # then
        core.ticked()
        self.assertEqual([], pool)
        self.assertEqual(task, core._processing)

        core.ticked()
        self.assertEqual([task], pool)
        self.assertEqual(None, core._processing)

        core.ticked()
        self.assertEqual([task], pool)
        self.assertEqual(None, core._processing)

        core.ticked()
        self.assertEqual([], pool)
        self.assertEqual(None, core._processing)
