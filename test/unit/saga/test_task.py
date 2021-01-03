from unittest import TestCase
from unittest.mock import Mock, call
from uuid import uuid4

from src.log import TimeLogger, LogContext
from src.sys.time.time import TimeDelta
from src.sys.time.duration import Duration
from src.saga.task import SystemOperation, Task


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
        logger = given_logging_context_that_provides_logger()
        operation1 = SystemOperation(to_process=True, name="1", duration=Duration(micros=2))
        operation2 = SystemOperation(to_process=False, name="2", duration=Duration(micros=1))

        task = Task(operations=[operation1, operation2], name="task")

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

        logger.log_task_processing.assert_has_calls([
            call(name="task", identifier=task.identifier),
            call(name="task", identifier=task.identifier)
        ])

    def test_is_complete_with_long_tick(self):
        # given
        logger = given_logging_context_that_provides_logger()
        operation = SystemOperation(to_process=True, name="1", duration=Duration(micros=2))
        task = Task(operations=[operation], name="task")

        # when
        task.ticked(time_delta=TimeDelta(Duration(micros=2)))

        # then
        self.assertTrue(task.is_complete())

        logger.log_task_processing.assert_called_once_with(name="task", identifier=task.identifier)

    def test_tick_should_throw_error_if_waiting(self):
        # given
        logger = given_logging_context_that_provides_logger()
        operation = SystemOperation(to_process=False, name="not to process", duration=Duration(micros=1))
        task = Task(operations=[operation])

        # when
        try:
            task.ticked(time_delta=TimeDelta(Duration(micros=1)))
        # then
        except ValueError:
            logger.log_task_processing.assert_not_called()
            return

        self.fail("Should throw exception")

    def test_wait_should_throw_error_if_processing(self):
        # given
        logger = given_logging_context_that_provides_logger()
        operation = SystemOperation(to_process=True, name="not to process", duration=Duration(micros=1))
        task = Task(operations=[operation])

        # when
        try:
            task.wait(time_delta=TimeDelta(Duration(micros=1)))
        # then
        except ValueError:
            logger.log_task_waiting.assert_not_called()
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
        logger = given_logging_context_that_provides_logger()
        task = Task(operations=[
            SystemOperation(to_process=True, name="1: processing", duration=Duration(micros=3)),
            SystemOperation(to_process=False, name="2: waiting", duration=Duration(micros=5))
        ], name="task")

        # when
        task.ticked(time_delta=TimeDelta(Duration(micros=3)))

        # then
        self.assertTrue(task.is_waiting())
        logger.log_task_processing.assert_called_once_with(name="task", identifier=task.identifier)

    def test_wait_should_be_skipped_if_time_delta_is_same_as_in_last_tick(self):
        # given
        logger = given_logging_context_that_provides_logger()
        task = Task(operations=[
            SystemOperation(to_process=True, name="1: processing", duration=Duration(micros=2)),
            SystemOperation(to_process=False, name="2: waiting", duration=Duration(micros=2))
        ], name="task")
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

        logger.log_task_processing.assert_called_once_with(name="task", identifier=task.identifier)
        logger.log_task_waiting.assert_called_once_with(name="task", identifier=task.identifier)

    def test_ticked_should_be_skipped_if_time_delta_is_same_as_in_last_wait(self):
        # given
        logger = given_logging_context_that_provides_logger()
        task = Task(operations=[
            SystemOperation(to_process=False, name="1: waiting", duration=Duration(micros=2)),
            SystemOperation(to_process=True, name="2: processing", duration=Duration(micros=2))
        ], name="task")
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

        logger.log_task_waiting.assert_called_once_with(name="task", identifier=task.identifier)
        logger.log_task_processing.assert_called_once_with(name="task", identifier=task.identifier)

    def test_is_waiting(self):
        # given
        logger = given_logging_context_that_provides_logger()
        task = Task(operations=[
            SystemOperation(to_process=True, name="1: processing1", duration=Duration(micros=1)),
            SystemOperation(to_process=False, name="2: waiting1", duration=Duration(micros=2)),
            SystemOperation(to_process=True, name="3: processing2", duration=Duration(micros=2)),
            SystemOperation(to_process=True, name="4: processing3", duration=Duration(micros=2)),
            SystemOperation(to_process=False, name="5: waiting2", duration=Duration(micros=1)),
            SystemOperation(to_process=False, name="6: waiting2", duration=Duration(micros=1)),
            SystemOperation(to_process=True, name="7: processing4", duration=Duration(micros=1))
        ], name="task")

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

        logger.log_task_processing.assert_has_calls([
            call(name="task", identifier=task.identifier),
            call(name="task", identifier=task.identifier),
            call(name="task", identifier=task.identifier),
            call(name="task", identifier=task.identifier),
            call(name="task", identifier=task.identifier),
            call(name="task", identifier=task.identifier)
        ])
        logger.log_task_waiting.assert_has_calls([
            call(name="task", identifier=task.identifier),
            call(name="task", identifier=task.identifier),
            call(name="task", identifier=task.identifier),
            call(name="task", identifier=task.identifier)
        ])


def given_logging_context_that_provides_logger() -> Mock:
    logger: Mock[TimeLogger] = Mock()
    LogContext.logger = lambda: logger
    return logger
