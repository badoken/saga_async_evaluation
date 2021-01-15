from typing import List
from unittest.mock import Mock

from src.sys.thread import Executable


def create_executables(count: int, ticks: int = 1) -> List[Executable]:
    return [create_executable(ticks, identifier) for identifier in range(count)]


def create_executable(ticks: int, identifier: int = 0) -> Executable:
    executable: Mock[Executable] = Mock(name=f"Executable{identifier}")

    is_complete_answers: List[bool] = [False for _ in range(ticks)]

    executable.ticked = Mock(
        side_effect=lambda duration: is_complete_answers.pop(0) if len(is_complete_answers) != 0 else None
    )
    executable.is_finished = lambda: len(is_complete_answers) == 0

    return executable
