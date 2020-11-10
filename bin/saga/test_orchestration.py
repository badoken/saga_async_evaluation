import collections
from typing import Tuple
from unittest import TestCase
from unittest.mock import Mock, call

from bin.saga.orchestration import Orchestrator
from bin.sys.core import Mode
from bin.sys.system import SystemFactory, System
from bin.sys.task import Task, SystemOperation
from bin.sys.time import TimeUnit


class TestOrchestrator(TestCase):
    def test_process(self):
        # given
        cores_factory, system = given_system_factory_that_produces_mock(expected_cores=2, expected_mode=Mode.ASYNC)
        orchestrator = Orchestrator(cores_count=2, processing_mode=Mode.ASYNC, system_factory=cores_factory)

        ticks_count = [0, 1, 2]
        system.tick = Mock(side_effect=lambda: ticks_count.pop(0))
        system.publish_task = Mock()

        saga = Mock()
        task1 = create_task(name="first")
        task2 = create_task(name="second")
        saga.last_incomplete_task = \
            lambda: {
                0: task1,
                1: task1,
                2: task2,
                None: None
            }[next(ticks_count.__iter__(), None)]

        mocks_manager = Mock()
        mocks_manager.attach_mock(system.tick, 'tick')
        mocks_manager.attach_mock(system.publish_task, 'publish')

        # when
        orchestrator.process(sagas=[saga])

        # then
        mocks_manager.assert_has_calls(
            calls=[
                call.publish(task1),
                call.tick(),
                call.tick(),
                call.publish(task2),
                call.tick()
            ]
        )


def create_task(name: str) -> Task:
    task = Task(operations=[SystemOperation(to_process=False, name=name, duration=TimeUnit(2))])
    return task


def given_system_factory_that_produces_mock(expected_cores: int, expected_mode: Mode) -> Tuple[SystemFactory, System]:
    factory = SystemFactory()
    system = Mock()
    factory.create = \
        lambda cores_count, processing_mode: system \
            if cores_count == expected_cores and processing_mode == expected_mode \
            else ValueError("Expected "
                            + str((expected_cores, expected_mode)) +
                            " but was " + str((cores_count, processing_mode))
                            )

    return factory, system
