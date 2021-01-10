from random import randint
from typing import List
from uuid import uuid4

from saga.simple_saga import SimpleSaga
from saga.task import Task, SystemOperation
from src.sys.time.duration import Duration


def _generate_command() -> Task:
    command_id = uuid4()
    request = SystemOperation(
        to_process=True,
        name=f"HTTP request[{command_id}]",
        duration=Duration.rand_between(
            start=Duration(micros=10),
            end=Duration(millis=60)
        )
    )
    wait = SystemOperation(
        to_process=False,
        name=f"wait for HTTP response[{command_id}]",
        duration=Duration.rand_between(
            start=Duration(millis=20),
            end=Duration(millis=700)
        )
    )
    response = SystemOperation(
        to_process=True,
        name=f"HTTP response[{command_id}]",
        duration=Duration.rand_between(
            start=Duration(millis=10),
            end=Duration(millis=100)
        )
    )
    return Task(
        operations=[request, wait, response],
        name=f"command[{command_id}]"
    )


def _generate_commands() -> List[Task]:
    return [_generate_command() for _ in range(randint(3, 10))]


def generate_saga() -> SimpleSaga:
    return SimpleSaga(
        tasks=_generate_commands(),
        name=f"saga{uuid4()}"
    )
