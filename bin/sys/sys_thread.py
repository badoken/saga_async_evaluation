from abc import abstractmethod
from typing import List

from bin.saga.task.task import Task
from bin.sys.time.time import TimeAffected


class SysThread(TimeAffected):
    @abstractmethod
    def is_finished(self) -> bool: pass

    @abstractmethod
    def get_current_tasks(self) -> List[Task]: pass
