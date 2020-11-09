from unittest import TestCase

from bin.sys.time import TimeUnit
from bin.sys.task import SystemOperation, Task


class TestSystemOperation(TestCase):
    def test_post_init_should_fail_if_there_is_non_positive_duration(self):
        for duration in [TimeUnit(-5), TimeUnit(-1), TimeUnit(0)]:
            # when
            try:
                SystemOperation(to_process=True, name="1", duration=duration)
            # then
            except ValueError:
                return

            self.fail("Should throw exception")


class TestTask(TestCase):
    def test_post_init_should_fail_if_there_is_no_operations(self):
        # given
        operations = []

        # when
        try:
            Task(operations=operations)
        # then
        except ValueError:
            return

        self.fail("Should throw exception")

    def test_is_complete(self):
        # given
        operation1 = SystemOperation(to_process=True, name="1", duration=TimeUnit(2))
        operation2 = SystemOperation(to_process=False, name="2", duration=TimeUnit(1))

        task = Task(operations=[operation1, operation2])

        # then
        self.assertFalse(task.is_complete())

        task.ticked()
        self.assertFalse(task.is_complete())
        task.ticked()
        self.assertFalse(task.is_complete())
        task.processing = True

        # 1
        task.ticked()
        self.assertFalse(task.is_complete())
        task.ticked()
        self.assertFalse(task.is_complete())

        # 2
        task.ticked()
        self.assertTrue(task.is_complete())
        self.assertTrue(task.is_complete())

    def test_is_waiting_when_first_operation_is_not_to_process(self):
        # given
        operation = SystemOperation(to_process=False, name="not to process", duration=TimeUnit(1))

        task = Task(operations=[operation])

        # then
        task.processing = True
        self.assertTrue(task.is_waiting())

    def test_is_waiting(self):
        # given
        task = Task(operations=[
            SystemOperation(to_process=True, name="1: processing1", duration=TimeUnit(1)),
            SystemOperation(to_process=False, name="2: waiting1", duration=TimeUnit(2)),
            SystemOperation(to_process=True, name="3: processing2", duration=TimeUnit(2)),
            SystemOperation(to_process=True, name="4: processing3", duration=TimeUnit(2)),
            SystemOperation(to_process=False, name="5: waiting2", duration=TimeUnit(1)),
            SystemOperation(to_process=False, name="6: waiting2", duration=TimeUnit(1)),
            SystemOperation(to_process=True, name="7: processing4", duration=TimeUnit(1))
        ])

        # then
        task.processing = True
        self.assertFalse(task.is_waiting())

        # 1
        task.ticked()
        self.assertTrue(task.is_waiting())

        # 2
        task.ticked()
        self.assertTrue(task.is_waiting())
        task.ticked()
        self.assertFalse(task.is_waiting())

        task.processing = False

        task.ticked()
        self.assertTrue(task.is_waiting())
        task.ticked()
        self.assertTrue(task.is_waiting())
        task.ticked()
        self.assertTrue(task.is_waiting())

        # 3
        task.processing = True

        task.ticked()
        self.assertFalse(task.is_waiting())

        task.processing = False

        task.ticked()
        self.assertTrue(task.is_waiting())

        task.processing = True

        task.ticked()
        self.assertFalse(task.is_waiting())

        # 4
        task.ticked()
        self.assertFalse(task.is_waiting())
        task.ticked()
        self.assertTrue(task.is_waiting())

        # 5
        task.ticked()
        self.assertTrue(task.is_waiting())

        # 6
        task.ticked()
        self.assertFalse(task.is_waiting())

        # 7
        task.ticked()
        self.assertTrue(task.is_waiting())
        task.ticked()
        self.assertTrue(task.is_waiting())
        self.assertTrue(task.is_waiting())
