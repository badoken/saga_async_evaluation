from dataclasses import dataclass
from typing import List

from bin.sys.core import Mode, CoreFactory
from bin.sys.task import Task
from bin.sys.time import TimeUnit


@dataclass
class System:
    cores_count: int
    processing_mode: Mode
    tasks_pool: List[Task]
    core_factory: CoreFactory = CoreFactory()

    def __post_init__(self):
        self._work_time = TimeUnit(0)
        self._cores = self.core_factory.new(
            count=self.cores_count,
            unassigned_tasks_pool=self.tasks_pool,
            mode=self.processing_mode
        )

    def tick(self):
        self._work_time.increment()

        for core in self._cores:
            core.ticked()

        for task in self.tasks_pool:
            task.ticked()
