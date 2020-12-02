from abc import abstractmethod
from typing import Optional

from bin.sys.task import Task
from bin.sys.time import TimeAffected


class SysThread(TimeAffected):
    @abstractmethod
    def is_finished(self) -> bool: pass

    @abstractmethod
    def set_processing(self, is_processing: bool): pass

    @abstractmethod
    def get_current_task(self) -> Optional[Task]: pass
