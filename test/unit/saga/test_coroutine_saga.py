from typing import List
from unittest import TestCase
from unittest.mock import Mock, call, ANY

from src.saga.coroutine_saga import CoroutineSaga
from src.sys.thread import Executable
from src.saga.task import Task
from src.sys.time.time import TimeDelta
from src.sys.time.duration import Duration


class TestCoroutineSaga(TestCase):
    def test_init_should_throw_error_if_a_coroutine_specified_as_param(self):
        # given
        saga = [executable("1"), CoroutineSaga(executables(1)), executable("3")]

        # when
        try:
            CoroutineSaga(saga)
        # then
        except ValueError:
            return

        self.fail("Should throw exception")

    def test_ticked_should_tick_one_executable_while_it_is_not_waiting(self):
        # given
        executable1, executable2 = executables(2)
        given_current_task_in_exectutable_is_not_waiting(executable_to_stub=executable1, not_waiting_ticks=3)

        coroutine = CoroutineSaga(executables=[executable1, executable2])

        mock_manager = Mock()
        mock_manager.attach_mock(executable1.ticked, "ticked1")
        mock_manager.attach_mock(executable2.ticked, "ticked2")

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

    def test_ticked_should_tick_no_executables_if_all_are_waiting(self):
        # given
        executable1, executable2 = executables(2)
        given_current_task_in_exectutable_is_not_waiting(executable_to_stub=executable1, not_waiting_ticks=0)
        given_current_task_in_exectutable_is_not_waiting(executable_to_stub=executable2, not_waiting_ticks=0)

        coroutine = CoroutineSaga(executables=[executable1, executable2])

        mock_manager = Mock()
        mock_manager.attach_mock(executable1.ticked, "ticked1")
        mock_manager.attach_mock(executable2.ticked, "ticked2")

        # when
        for _ in range(4):
            coroutine.ticked(time_delta=TimeDelta(Duration(micros=1)))

        # then
        call.ticked1.assert_not_called()
        call.ticked2.assert_not_called()

    def test_ticked_should_tick_one_executable_while_it_is_not_finished(self):
        # given
        executable1, executable2 = executables(2)
        given_current_task_in_executable_is_not_finished(executable_to_stub=executable1, not_finished_ticks=3)

        coroutine = CoroutineSaga(executables=[executable1, executable2])

        mock_manager = Mock()
        mock_manager.attach_mock(executable1.ticked, "ticked1")
        mock_manager.attach_mock(executable2.ticked, "ticked2")

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

    def test_ticked_should_tick_no_executables_if_all_are_finished(self):
        # given
        executable1, executable2 = executables(2)
        given_current_task_in_executable_is_not_finished(executable_to_stub=executable1, not_finished_ticks=0)

        coroutine = CoroutineSaga(executables=[executable1, executable2])

        mock_manager = Mock()
        mock_manager.attach_mock(executable1.ticked, "ticked1")
        mock_manager.attach_mock(executable2.ticked, "ticked2")

        # when
        for _ in range(4):
            coroutine.ticked(time_delta=TimeDelta(Duration(micros=1)))

        # then
        call.ticked1.assert_not_called()
        call.ticked2.assert_not_called()

    def test_ticked_should_finish_when_all_executables_are_finished(self):
        # given
        executable1, executable2 = executables(2)
        given_current_task_in_executable_is_not_finished(executable_to_stub=executable1, not_finished_ticks=2)
        given_current_task_in_executable_is_not_finished(executable_to_stub=executable2, not_finished_ticks=1)

        coroutine = CoroutineSaga(executables=[executable1, executable2])

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

    def test_get_current_tasks_should_return_current_tasks_of_all_executables(self):
        # given
        executable1, executable2 = executables(2)

        executable1_task: Task = Mock()
        executable1.get_current_tasks = lambda: [executable1_task]

        executable2_task: Task = Mock()
        executable2.get_current_tasks = lambda: [executable2_task]

        coroutine = CoroutineSaga(executables=[executable1, executable2])

        # when
        actual = coroutine.get_current_tasks()

        # then
        self.assertEqual([executable1_task, executable2_task], actual)


def executables(count: int) -> List[Executable]:
    return [executable(name=f"thread {i + 1}") for i in range(count)]


def executable(name: str = "thread") -> Executable:
    mock: Executable = Mock(name=name)
    mock.is_finished = lambda: False

    task: Task = Mock()
    task.is_waiting = lambda: False
    mock.get_current_tasks = lambda: [task]
    return mock


def given_current_task_in_exectutable_is_not_waiting(executable_to_stub: Executable, not_waiting_ticks: int):
    is_waiting_answers = [False for _ in range(not_waiting_ticks)]
    current_task: Task = Mock()
    executable_to_stub.get_current_tasks = lambda: [current_task]
    executable_to_stub.ticked = Mock(side_effect=lambda time_delta: is_waiting_answers.pop() if is_waiting_answers else None)
    current_task.is_waiting = lambda: next(iter(is_waiting_answers), True)


def given_current_task_in_executable_is_not_finished(executable_to_stub: Executable, not_finished_ticks: int):
    is_finished_answered = [False for _ in range(not_finished_ticks)]
    executable_to_stub.ticked = Mock(side_effect=lambda time_delta: is_finished_answered.pop() if is_finished_answered else None)
    executable_to_stub.is_finished = lambda: next(iter(is_finished_answered), True)
