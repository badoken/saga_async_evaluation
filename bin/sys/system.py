from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import final


@dataclass
class TimeUnit:
    val: int

    def increment(self): self.val += 1


class TimeAffected(ABC):
    @abstractmethod
    def ticked(self): pass


@dataclass
class System:
    time: TimeUnit = TimeUnit(0)

    def tick(self): self.time.increment()
