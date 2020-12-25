from typing import List, Tuple

from unittest.mock import Mock, call, ANY

from unittest import TestCase

from bin.sys.core import Core, CoreFactory
from bin.sys.operation_system import OperationSystem, ProcessingMode
from bin.sys.sys_thread import SysThread
from bin.sys.task import Task
from bin.sys.time import Duration, TimeDelta


class TestOperationSystem(TestCase):
    def test_should_publish_all_tasks_to_core_if_in_overloaded_mode(self):
        # given
        factory = core_factory()
        core1 = core_mock(factory)
        core2 = core_mock(factory)

        system = OperationSystem(cores_count=2, processing_mode=ProcessingMode.OVERLOADED_CORES, core_factory=factory)

        thread1, thread2, thread3, thread4 = sys_threads(4)

        # when
        system.publish([thread1, thread2, thread3, thread4])
        system.tick(duration=Duration(micros=1))
        system.tick(duration=Duration(micros=1))

        # then
        core1.assign.assert_has_calls([call(thread1), call(thread3)])
        core1.ticked.assert_has_calls([
            call(time_delta=TimeDelta(duration=Duration(micros=1), identifier=ANY)),
            call(time_delta=TimeDelta(duration=Duration(micros=1), identifier=ANY))
        ])
        core2.assign.assert_has_calls([call(thread2), call(thread4)])
        core2.ticked.assert_has_calls([
            call(time_delta=TimeDelta(duration=Duration(micros=1), identifier=ANY)),
            call(time_delta=TimeDelta(duration=Duration(micros=1), identifier=ANY))
        ])

    def test_should_tick_cores_and_trigger_waiting_tasks(self):
        # given
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
        system.tick(duration=Duration(micros=1))
        task.is_waiting = lambda: False
        system.tick(duration=Duration(micros=1))

        # then
        mock_manager.assert_has_calls(
            calls=[
                call.ticked(time_delta=TimeDelta(duration=Duration(micros=1), identifier=ANY)),
                call.wait(time_delta=TimeDelta(duration=Duration(micros=1), identifier=ANY)),
                call.ticked(time_delta=TimeDelta(duration=Duration(micros=1), identifier=ANY)),
            ]
        )
        ticked_first_call_arg: TimeDelta = mock_manager.ticked.call_args_list[0][1]['time_delta']
        ticked_second_call_arg: TimeDelta = mock_manager.ticked.call_args_list[1][1]['time_delta']
        wait_call_arg: TimeDelta = mock_manager.wait.call_args_list[0][1]['time_delta']

        self.assertEqual(ticked_first_call_arg, wait_call_arg)

        self.assertEqual(ticked_first_call_arg.duration, ticked_second_call_arg.duration)
        self.assertNotEqual(ticked_first_call_arg.identifier, ticked_second_call_arg.identifier)

    def test_should_publish_all_tasks_to_core_if_in_fixed_pool_mode(self):
        # given
        factory = core_factory()
        core1 = core_mock(factory)
        core2 = core_mock(factory)

        system = OperationSystem(cores_count=2, processing_mode=ProcessingMode.FIXED_POOL_SIZE, core_factory=factory)

        thread1, thread2, thread3, thread4 = sys_threads(4)

        # when
        system.publish([thread1, thread2, thread3, thread4])
        system.tick(duration=Duration(micros=1))

        # then
        core1.assign.assert_called_once_with(thread1)
        core1.ticked.assert_called_once_with(time_delta=TimeDelta(duration=Duration(micros=1), identifier=ANY))
        reset_core_mock(core1)
        core2.assign.assert_called_once_with(thread2)
        core2.ticked.assert_called_once_with(time_delta=TimeDelta(duration=Duration(micros=1), identifier=ANY))
        reset_core_mock(core2)

        # when
        core1.is_starving = lambda: True
        core2.is_starving = lambda: True
        system.tick(duration=Duration(micros=1))

        # then
        core1.assign.assert_called_once_with(thread3)
        core1.ticked.assert_called_once_with(time_delta=TimeDelta(duration=Duration(micros=1), identifier=ANY))
        core2.assign.assert_called_once_with(thread4)
        core2.ticked.assert_called_once_with(time_delta=TimeDelta(Duration(micros=1), identifier=ANY))
        core2.ticked.assert_called_once_with(time_delta=TimeDelta(Duration(micros=1), identifier=ANY))

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


def sys_threads(count: int) -> List[SysThread]:
    return [sys_thread(name="thread " + str(i)) for i in range(count)]


def sys_thread(name: str = "thread") -> SysThread:
    thread: SysThread = Mock(name=name)
    thread.get_current_tasks = lambda: []
    return thread


def reset_core_mock(core: Core):
    core.assign.reset_mock()
    core.ticked.reset_mock()
