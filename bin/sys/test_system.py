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
        core_factory, core = self.core_factory_that_produces_core()
        system = System(core_factory=core_factory, cores_count=1, processing_mode=Mode.ASYNC, tasks_pool=[])

        # when
        system.tick()

        # then
        core.ticked.assert_called_once()

    def test_tick_should_tick_unassigned_tasks(self):
        # given
        task = Task(operations=[SystemOperation(False, "op", TimeUnit(1))])
        task.ticked = Mock()

        task_pool = [task]

        core_factory, _ = self.core_factory_that_produces_core()
        system = System(core_factory=core_factory, cores_count=1, processing_mode=Mode.ASYNC, tasks_pool=task_pool)

        # then
        system.tick()
        task.ticked.assert_called_once()

        task_pool.pop(0)
        system.tick()
        task.ticked.assert_called_once()

        task_pool.append(task)
        system.tick()
        task.ticked.assert_has_calls(calls=[call(), call()])

    @staticmethod
    def core_factory_that_produces_core() -> Tuple[CoreFactory, Core]:
        core = Core(unassigned_tasks_pool=[], mode=Mode.ASYNC)
        core.ticked = Mock()
        core_factory = CoreFactory()
        core_factory.new = Mock(return_value=[core])
        return core_factory, core
