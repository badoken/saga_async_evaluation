from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID, uuid4

from src.sys.time.duration import Duration


@dataclass
class TimeDelta:
    duration: Duration
    identifier: UUID = None

    def __post_init__(self):
        if self.identifier is None:
            self.identifier = uuid4()


class TimeAffected(ABC):
    @abstractmethod
    def ticked(self, time_delta: TimeDelta): pass


class Constants:
    @staticmethod
    def core() -> Duration:
        pass  # TODO
