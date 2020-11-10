from typing import List, Tuple

from mock import Mock, call
from unittest import TestCase

from bin.sys.core import Core, Mode, CoreFactory
from bin.sys.system import System
from bin.sys.task import Task, SystemOperation
from bin.sys.time import TimeUnit


class TestSystem(TestCase):
    def test_tick_should_tick_cores_each_time(self):
        # given
        core_factory, core = core_factory_that_produces_mocked_core()
        system = System(core_factory=core_factory, cores_count=1, processing_mode=Mode.ASYNC)

        # when
        system.tick()

        # then
        core.ticked.assert_called_once()

    def test_tick_should_tick_unassigned_tasks(self):
        # given
        task = Task(operations=[SystemOperation(False, "op", TimeUnit(1))])
        task.ticked = Mock()

        core_factory, core = core_factory_that_produces_mocked_core()
        system = System(core_factory=core_factory, cores_count=1, processing_mode=Mode.ASYNC)

        # then
        system.publish_task(task)

        system.tick()
        task.ticked.assert_called_once()

        core.unassigned_tasks_pool.pop(0)
        system.tick()
        task.ticked.assert_called_once()

        system.publish_task(task)
        system.tick()
        task.ticked.assert_has_calls(calls=[call(), call()])


def core_factory_that_produces_mocked_core() -> Tuple[CoreFactory, Core]:
    core = Core(unassigned_tasks_pool=[], mode=Mode.ASYNC)
    core.ticked = Mock()

    core_factory = CoreFactory()
    core_factory.new = lambda count, unassigned_tasks_pool, mode: \
        [core_with_overwritten_tasks_pool(core, unassigned_tasks_pool)] if count is 1 else ValueError(
            "Count should be 1")

    return core_factory, core


def core_with_overwritten_tasks_pool(core, tasks_pool) -> Core:
    core.unassigned_tasks_pool = tasks_pool
    return core
