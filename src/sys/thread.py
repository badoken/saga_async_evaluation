from abc import abstractmethod
from typing import List

from src.saga.task import Task
from src.sys.time.time import TimeAffected


class Thread(TimeAffected):
    @abstractmethod
    def is_finished(self) -> bool: pass

    @abstractmethod
    def get_current_tasks(self) -> List[Task]: pass
