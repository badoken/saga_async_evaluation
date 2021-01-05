from typing import List

from unittest.mock import Mock, call, ANY, patch

from unittest import TestCase

from src.log import LogContext
from src.sys.core import Core, CoreFactory
from src.sys.operation_system import OperationSystem, ProcessingMode
from src.sys.thread import Thread
from src.saga.task import Task
from src.sys.time.time import TimeDelta
from src.sys.time.duration import Duration


class TestOperationSystem(TestCase):

    log_context_shift_time = LogContext.shift_time

    @classmethod
    def tearDownClass(cls):
        LogContext.shift_time = cls.log_context_shift_time

    @patch("src.sys.operation_system.LogContext")
    def test_should_publish_all_tasks_to_core_if_in_overloaded_mode(self, log_context_class):
        # given
        shift_time_method = log_context_class.shift_time

        factory = core_factory()
        core1 = core_mock(factory)
        core2 = core_mock(factory)

        system = OperationSystem(cores_count=2, processing_mode=ProcessingMode.OVERLOADED_CORES, core_factory=factory)

        thread1, thread2, thread3, thread4 = sys_threads(4)

        # when
        system.publish([thread1, thread2, thread3, thread4])
        system.tick(duration=Duration(nanos=1))
        system.tick(duration=Duration(nanos=1))

        # then
        core1.assign.assert_has_calls([call(thread1), call(thread3)])
        core1.ticked.assert_has_calls([
            call(time_delta=TimeDelta(duration=Duration(nanos=1), identifier=ANY)),
            call(time_delta=TimeDelta(duration=Duration(nanos=1), identifier=ANY))
        ])
        core2.assign.assert_has_calls([call(thread2), call(thread4)])
        core2.ticked.assert_has_calls([
            call(time_delta=TimeDelta(duration=Duration(nanos=1), identifier=ANY)),
            call(time_delta=TimeDelta(duration=Duration(nanos=1), identifier=ANY))
        ])
        log_context_class.shift_time.assert_has_calls([call(), call()])
        shift_time_method.assert_has_calls([call(), call()])

    def test_should_tick_cores_and_trigger_waiting_tasks(self):
        # given
        shift_time_method = given_shift_time_is_a_mock()

        factory = core_factory()
        core = core_mock(factory)
        system = OperationSystem(cores_count=1, processing_mode=ProcessingMode.OVERLOADED_CORES, core_factory=factory)

        task: Task = Mock()
        task.is_waiting = lambda: True
        task.wait = Mock()

        thread = sys_thread()
        thread.get_current_tasks = lambda: [task]

        system.publish([thread])

        mock_manager = Mock()
        mock_manager.attach_mock(core.ticked, "ticked")
        mock_manager.attach_mock(task.wait, "wait")

        # when
        system.tick(duration=Duration(nanos=1))
        task.is_waiting = lambda: False
        system.tick(duration=Duration(nanos=1))

        # then
        mock_manager.assert_has_calls(
            calls=[
                call.ticked(time_delta=TimeDelta(duration=Duration(nanos=1), identifier=ANY)),
                call.wait(time_delta=TimeDelta(duration=Duration(nanos=1), identifier=ANY)),
                call.ticked(time_delta=TimeDelta(duration=Duration(nanos=1), identifier=ANY)),
            ]
        )
        ticked_first_call_arg: TimeDelta = mock_manager.ticked.call_args_list[0][1]['time_delta']
        ticked_second_call_arg: TimeDelta = mock_manager.ticked.call_args_list[1][1]['time_delta']
        wait_call_arg: TimeDelta = mock_manager.wait.call_args_list[0][1]['time_delta']

        self.assertEqual(ticked_first_call_arg, wait_call_arg)

        self.assertEqual(ticked_first_call_arg.duration, ticked_second_call_arg.duration)
        self.assertNotEqual(ticked_first_call_arg.identifier, ticked_second_call_arg.identifier)

        shift_time_method.assert_has_calls([call(), call()])

    def test_should_publish_all_tasks_to_core_if_in_fixed_pool_mode(self):
        # given
        shift_time_method = given_shift_time_is_a_mock()

        factory = core_factory()
        core1 = core_mock(factory)
        core2 = core_mock(factory)

        system = OperationSystem(cores_count=2, processing_mode=ProcessingMode.FIXED_POOL_SIZE, core_factory=factory)

        thread1, thread2, thread3, thread4 = sys_threads(4)

        # when
        system.publish([thread1, thread2, thread3, thread4])
        system.tick(duration=Duration(nanos=1))

        # then
        core1.assign.assert_called_once_with(thread1)
        core1.ticked.assert_called_once_with(time_delta=TimeDelta(duration=Duration(nanos=1), identifier=ANY))
        reset_core_mock(core1)
        core2.assign.assert_called_once_with(thread2)
        core2.ticked.assert_called_once_with(time_delta=TimeDelta(duration=Duration(nanos=1), identifier=ANY))
        reset_core_mock(core2)

        # when
        core1.is_starving = lambda: True
        core2.is_starving = lambda: True
        system.tick(duration=Duration(nanos=1))

        # then
        core1.assign.assert_called_once_with(thread3)
        core1.ticked.assert_called_once_with(time_delta=TimeDelta(duration=Duration(nanos=1), identifier=ANY))
        core2.assign.assert_called_once_with(thread4)
        core2.ticked.assert_called_once_with(time_delta=TimeDelta(Duration(nanos=1), identifier=ANY))
        core2.ticked.assert_called_once_with(time_delta=TimeDelta(Duration(nanos=1), identifier=ANY))

        shift_time_method.assert_has_calls([call(), call()])

    def test_work_is_done_should_return_false_if_cores_are_not_starving(self):
        # given
        factory = core_factory()
        core1 = core_mock(factory)
        core1.is_starving = lambda: False
        system = OperationSystem(cores_count=1, processing_mode=ProcessingMode.FIXED_POOL_SIZE, core_factory=factory)

        # when
        result = system.work_is_done()

        # then
        self.assertFalse(result)

    def test_work_is_done_should_return_false_if_there_are_tasks_in_the_pool(self):
        # given
        factory = core_factory()
        core1 = core_mock(factory)
        core1.is_starving = lambda: True
        system = OperationSystem(cores_count=1, processing_mode=ProcessingMode.FIXED_POOL_SIZE, core_factory=factory)

        threads = sys_threads(10)

        # when
        system.publish(threads)
        result = system.work_is_done()

        # then
        self.assertFalse(result)

    def test_work_is_done_should_return_true_if_there_are_no_tasks_in_the_pool_and_cores_are_starving(self):
        # given
        factory = core_factory()
        core1 = core_mock(factory)
        core1.is_starving = lambda: True
        system = OperationSystem(cores_count=1, processing_mode=ProcessingMode.FIXED_POOL_SIZE, core_factory=factory)

        # when
        result = system.work_is_done()

        # then
        self.assertTrue(result)


def core_factory() -> CoreFactory:
    factory = CoreFactory()
    mocks = []
    factory.mocks = mocks
    factory.new = lambda count, processing_interval: \
        mocks if count is len(mocks) else ValueError("Count should be " + str(len(mocks)))

    return factory


def core_mock(factory: CoreFactory) -> Core:
    core1 = Core(processing_interval=Duration(20), identifier=1)
    core1.ticked = Mock()
    core1.assign = Mock(wraps=core1.assign)
    factory.mocks.append(core1)
    return core1


def sys_threads(count: int) -> List[Thread]:
    return [sys_thread(name="thread " + str(i)) for i in range(count)]


def sys_thread(name: str = "thread") -> Thread:
    thread: Thread = Mock(name=name)
    thread.get_current_tasks = lambda: []
    return thread


def reset_core_mock(core: Core):
    core.assign.reset_mock()
    core.ticked.reset_mock()


def given_shift_time_is_a_mock() -> Mock:
    shift_time_method: Mock = Mock()
    LogContext.shift_time = shift_time_method
    return shift_time_method
