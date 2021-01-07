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
        name="HTTP request[" + str(command_id) + "]",
        duration=Duration.rand_between(
            start=Duration(micros=10),
            end=Duration(millis=60)
        )
    )
    wait = SystemOperation(
        to_process=True,
        name="wait for HTTP response[" + str(command_id) + "]",
        duration=Duration.rand_between(
            start=Duration(millis=20),
            end=Duration(millis=700)
        )
    )
    response = SystemOperation(
        to_process=True,
        name="HTTP response[" + str(command_id) + "]",
        duration=Duration.rand_between(
            start=Duration(millis=10),
            end=Duration(millis=100)
        )
    )
    return Task(
        operations=[request, wait, response],
        name="command[" + str(command_id) + "]"
    )


def _generate_fs_write() -> Task:
    command_id = uuid4()

    return Task(
        operations=[
            operation

            for block_write_operations
            in [
                _generate_fs_data_block_write(block_number=i, command_id=command_id)
                for i
                in range(randint(1, 4))
            ]

            for operation
            in block_write_operations
        ],
        name="command[" + str(command_id) + "]"
    )


def _generate_fs_data_block_write(block_number: int, command_id: uuid4()) -> List[SystemOperation]:
    return [
        SystemOperation(
            to_process=True,
            name="Data block " + str(block_number) + " write [" + str(command_id) + "]",
            duration=Duration.rand_between(
                start=Duration(micros=3),
                end=Duration(micros=5)
            )
        ),
        SystemOperation(
            to_process=False,
            name="Data block " + str(block_number) + " wait [" + str(command_id) + "]",
            duration=Duration.rand_between(
                start=Duration(micros=8),
                end=Duration(micros=11)
            )
        ),
        SystemOperation(
            to_process=False,
            name="Data block " + str(block_number) + " jbd2 wait [" + str(command_id) + "]",
            duration=Duration.rand_between(
                start=Duration(micros=20),
                end=Duration(micros=24)
            )
        )
    ]


def _generate_command_and_fs_operation(data_preservation: bool) -> List[Task]:
    result: List[Task] = [_generate_command()]
    # TODO data amount dependency between these two
    if data_preservation:
        result.append(_generate_fs_write())
    return result


def generate_saga(data_preservation: bool) -> SimpleSaga:
    return SimpleSaga(
        tasks=[
            task
            for task
            in _generate_command_and_fs_operation(data_preservation)
        ],
        name="saga" + str(uuid4())
    )
