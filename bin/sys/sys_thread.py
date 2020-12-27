from abc import abstractmethod
from typing import Optional, List

from bin.sys.task import Task
from bin.sys.time import TimeAffected


class SysThread(TimeAffected):
    @abstractmethod
    def is_finished(self) -> bool: pass

    @abstractmethod
    def get_current_tasks(self) -> List[Task]: pass