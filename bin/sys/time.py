from abc import ABC, abstractmethod
from dataclasses import dataclass


class TimeAffected(ABC):
    @abstractmethod
    def ticked(self): pass


@dataclass
class TimeUnit:
    val: int

    def increment(self): self.val += 1
