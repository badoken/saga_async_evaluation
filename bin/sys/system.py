from dataclasses import dataclass
from typing import List

from bin.sys.core import Mode, CoreFactory
from bin.sys.task import Task
from bin.sys.time import TimeUnit


@dataclass
class System:
    cores_count: int
    processing_mode: Mode
    core_factory: CoreFactory = CoreFactory()

    def __post_init__(self):
        self._work_time = TimeUnit(0)
        self._shared_tasks_pool: List[Task] = []
        self._cores = self.core_factory.new(
            count=self.cores_count,
            unassigned_tasks_pool=self._shared_tasks_pool,
            mode=self.processing_mode
        )

    def publish_task(self, task: Task):
        self._shared_tasks_pool.append(task)

    def tick(self):
        self._work_time.increment()

        for core in self._cores:
            core.ticked()

        for task in self._shared_tasks_pool:
            task.ticked()


class SystemFactory:
    # noinspection PyMethodMayBeStatic
    def create(self, cores_count: int, processing_mode: Mode) -> System:
        return System(cores_count=cores_count, processing_mode=processing_mode)
