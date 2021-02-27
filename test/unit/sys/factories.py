from __future__ import annotations
from typing import List
from unittest.mock import Mock

from src.saga.task import Task
from src.sys.thread import Executable


def create_executables(count: int, ticks: int = 1) -> List[Mock[Executable]]:
    return [create_executable(ticks, identifier) for identifier in range(count)]


def create_executable(ticks: int, waits: int = 0, identifier: int = 0) -> Mock[Executable]:
    executable: Mock[Executable] = Mock(name=f"Executable{identifier}")

    is_complete_answers: List[str] = ["work" for _ in range(ticks)]
    is_complete_answers.extend(["wait" for _ in range(waits)])

    executable.ticked = Mock(
        side_effect=lambda duration: is_complete_answers.pop(0) if len(is_complete_answers) != 0 else None
    )
    executable.is_finished = lambda: len(is_complete_answers) == 0
    executable.get_current_tasks = lambda: \
        [_create_dummy_task(is_waiting=next(iter(is_complete_answers), "work") == "wait")]

    return executable


def _create_dummy_task(is_waiting: bool) -> Mock[Task]:
    task: Mock[Task] = Mock()
    task.is_waiting = lambda: is_waiting
    return task
