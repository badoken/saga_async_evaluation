from dataclasses import dataclass
from typing import List, Optional

from bin.sys.task import Task


@dataclass
class Saga:
    tasks: List[Task]

    def is_finished(self) -> bool:
        return all(task.is_complete() for task in self.tasks)

    def last_incomplete_task(self) -> Optional[Task]:
        return next((task for task in self.tasks if not task.is_complete()), None)
