from unittest import TestCase
from uuid import uuid4

from bin.sys.time import Duration, TimeDelta
from bin.sys.task import SystemOperation, Task


class TestSystemOperation(TestCase):
    def test_post_init_should_fail_if_there_is_non_positive_duration(self):
        for duration in [Duration(micros=-5), Duration(micros=-1), Duration(micros=0)]:
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
        operation1 = SystemOperation(to_process=True, name="1", duration=Duration(micros=2))
        operation2 = SystemOperation(to_process=False, name="2", duration=Duration(micros=1))

        task = Task(operations=[operation1, operation2])

        # then
        self.assertFalse(task.is_complete())

        # 1
        task.ticked(time_delta=TimeDelta(Duration(micros=1)))
        self.assertFalse(task.is_complete())
        task.ticked(time_delta=TimeDelta(Duration(micros=1)))
        self.assertFalse(task.is_complete())

        # 2
        task.wait(time_delta=TimeDelta(Duration(micros=1)))
        self.assertTrue(task.is_complete())
        self.assertTrue(task.is_complete())

    def test_is_complete_with_long_tick(self):
        # given
        operation = SystemOperation(to_process=True, name="1", duration=Duration(micros=2))
        task = Task(operations=[operation])

        # when
        task.ticked(time_delta=TimeDelta(Duration(micros=2)))

        # then
        self.assertTrue(task.is_complete())

    def test_tick_should_throw_error_if_waiting(self):
        # given
        operation = SystemOperation(to_process=False, name="not to process", duration=Duration(micros=1))
        task = Task(operations=[operation])

        # when
        try:
            task.ticked(time_delta=TimeDelta(Duration(micros=1)))
        # then
        except ValueError:
            return

        self.fail("Should throw exception")

    def test_wait_should_throw_error_if_processing(self):
        # given
        operation = SystemOperation(to_process=True, name="not to process", duration=Duration(micros=1))
        task = Task(operations=[operation])

        # when
        try:
            task.wait(time_delta=TimeDelta(Duration(micros=1)))
        # then
        except ValueError:
            return

        self.fail("Should throw exception")

    def test_is_waiting_when_first_operation_is_not_to_process(self):
        # given
        operation = SystemOperation(to_process=False, name="not to process", duration=Duration(micros=1))

        task = Task(operations=[operation])

        # then
        self.assertTrue(task.is_waiting())

    def test_is_waiting_with_long_tick(self):
        # given
        task = Task(operations=[
            SystemOperation(to_process=True, name="1: processing", duration=Duration(micros=3)),
            SystemOperation(to_process=False, name="2: waiting", duration=Duration(micros=5))
        ])

        # when
        task.ticked(time_delta=TimeDelta(Duration(micros=3)))

        # then
        self.assertTrue(task.is_waiting())

    def test_wait_should_be_skipped_if_time_delta_is_same_as_in_last_tick(self):
        # given
        task = Task(operations=[
            SystemOperation(to_process=True, name="1: processing", duration=Duration(micros=2)),
            SystemOperation(to_process=False, name="2: waiting", duration=Duration(micros=2))
        ])
        delta_id = uuid4()

        # then
        # 1
        task.ticked(time_delta=TimeDelta(Duration(micros=2), identifier=delta_id))
        self.assertTrue(task.is_waiting())
        self.assertFalse(task.is_complete())
        # 2 with same delta
        task.wait(time_delta=TimeDelta(Duration(micros=2), identifier=delta_id))
        self.assertTrue(task.is_waiting())
        self.assertFalse(task.is_complete())
        # 2 with different delta
        task.wait(time_delta=TimeDelta(Duration(micros=2)))
        self.assertTrue(task.is_waiting())
        self.assertTrue(task.is_complete())

    def test_ticked_should_be_skipped_if_time_delta_is_same_as_in_last_wait(self):
        # given
        task = Task(operations=[
            SystemOperation(to_process=False, name="1: waiting", duration=Duration(micros=2)),
            SystemOperation(to_process=True, name="2: processing", duration=Duration(micros=2))
        ])
        delta_id = uuid4()

        # then
        # 1
        task.wait(time_delta=TimeDelta(Duration(micros=2), identifier=delta_id))
        self.assertFalse(task.is_waiting())
        self.assertFalse(task.is_complete())
        # 2 with same delta
        task.ticked(time_delta=TimeDelta(Duration(micros=2), identifier=delta_id))
        self.assertFalse(task.is_waiting())
        self.assertFalse(task.is_complete())
        # 2 with different delta
        task.ticked(time_delta=TimeDelta(Duration(micros=2)))
        self.assertTrue(task.is_waiting())
        self.assertTrue(task.is_complete())

    def test_is_waiting(self):
        # given
        task = Task(operations=[
            SystemOperation(to_process=True, name="1: processing1", duration=Duration(micros=1)),
            SystemOperation(to_process=False, name="2: waiting1", duration=Duration(micros=2)),
            SystemOperation(to_process=True, name="3: processing2", duration=Duration(micros=2)),
            SystemOperation(to_process=True, name="4: processing3", duration=Duration(micros=2)),
            SystemOperation(to_process=False, name="5: waiting2", duration=Duration(micros=1)),
            SystemOperation(to_process=False, name="6: waiting2", duration=Duration(micros=1)),
            SystemOperation(to_process=True, name="7: processing4", duration=Duration(micros=1))
        ])

        # then
        self.assertFalse(task.is_waiting())

        # 1
        task.ticked(time_delta=TimeDelta(Duration(micros=1)))
        self.assertTrue(task.is_waiting())

        # 2
        task.wait(time_delta=TimeDelta(Duration(micros=1)))
        self.assertTrue(task.is_waiting())
        task.wait(time_delta=TimeDelta(Duration(micros=1)))
        self.assertFalse(task.is_waiting())

        # 3
        task.ticked(time_delta=TimeDelta(Duration(micros=1)))
        self.assertFalse(task.is_waiting())
        task.ticked(time_delta=TimeDelta(Duration(micros=1)))
        self.assertFalse(task.is_waiting())

        # 4
        task.ticked(time_delta=TimeDelta(Duration(micros=1)))
        self.assertFalse(task.is_waiting())
        task.ticked(time_delta=TimeDelta(Duration(micros=1)))
        self.assertTrue(task.is_waiting())

        # 5
        task.wait(time_delta=TimeDelta(Duration(micros=1)))
        self.assertTrue(task.is_waiting())

        # 6
        task.wait(time_delta=TimeDelta(Duration(micros=1)))
        self.assertFalse(task.is_waiting())

        # 7
        task.ticked(time_delta=TimeDelta(Duration(micros=1)))
        self.assertTrue(task.is_waiting())
        task.ticked(time_delta=TimeDelta(Duration(micros=1)))
        self.assertTrue(task.is_waiting())
        self.assertTrue(task.is_waiting())
