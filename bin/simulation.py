from copy import deepcopy
from pathlib import Path

from bin.saga.coroutines_orchestrator import CoroutinesOrchestrator
from bin.saga.threaded_orchestrator import ThreadedOrchestrator
from bin.saga.simple_saga import SimpleSaga
from bin.sys.operation_system import ProcessingMode
from bin.sys.task import Task, SystemOperation
from bin.sys.time import Duration, LogContext

tuff_task = Task(
    operations=[
        SystemOperation(to_process=True, name="[1]op2.1", duration=Duration(10)),
        SystemOperation(to_process=False, name="[1]wait2.1", duration=Duration(200)),
        SystemOperation(to_process=True, name="[1]op2.2", duration=Duration(20)),
        SystemOperation(to_process=False, name="[1]wait2.2", duration=Duration(100)),
        SystemOperation(to_process=True, name="[1]op2.3", duration=Duration(44))
    ],
    name="[1]tuff task"
)

sagas = [
    SimpleSaga(
        tasks=[
            Task(
                operations=[
                    SystemOperation(to_process=True, name="[1]op1.1", duration=Duration(1)),
                    SystemOperation(to_process=False, name="[1]wait1", duration=Duration(200)),
                    SystemOperation(to_process=True, name="[1]op1.2", duration=Duration(2))
                ],
                name="[1]simple task"
            )
        ],
        name="[1]"
    ),
    SimpleSaga(
        tasks=[
            Task(
                operations=[
                    SystemOperation(to_process=True, name="[1]op1.1", duration=Duration(1)),
                    SystemOperation(to_process=False, name="[1]wait1", duration=Duration(200)),
                    SystemOperation(to_process=True, name="[1]op1.2", duration=Duration(2))
                ],
                name="[1]simple task"
            )
        ],
        name="[1]"
    ),
    SimpleSaga(
        tasks=[
            Task(
                operations=[
                    SystemOperation(to_process=True, name="[1]op1.1", duration=Duration(1)),
                    SystemOperation(to_process=False, name="[1]wait1", duration=Duration(200)),
                    SystemOperation(to_process=True, name="[1]op1.2", duration=Duration(2))
                ],
                name="[1]simple task"
            )
        ],
        name="[1]"
    ),
]

overloaded_threads_orchestrator = ThreadedOrchestrator(cores_count=2, processing_mode=ProcessingMode.OVERLOADED_CORES)
fixed_pool_threads_orchestrator = ThreadedOrchestrator(cores_count=2, processing_mode=ProcessingMode.FIXED_POOL_SIZE)
coroutines_orchestrator = CoroutinesOrchestrator(cores_count=2)

LogContext.run_logging(
    log_name="Overloaded",
    action=lambda: overloaded_threads_orchestrator.process(deepcopy(sagas))
)

LogContext.run_logging(
    log_name="Fixed pool",
    action=lambda: fixed_pool_threads_orchestrator.process(deepcopy(sagas))
)

LogContext.run_logging(
    log_name="Coroutines",
    action=lambda: coroutines_orchestrator.process(deepcopy(sagas))
)
