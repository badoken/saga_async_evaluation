from bin.saga.orchestration import Orchestrator
from bin.saga.saga import Saga
from bin.sys.core import Mode
from bin.sys.task import Task, SystemOperation
from bin.sys.time import TimeUnit

sagas = [
    Saga(tasks=[
        Task(operations=[  # TODO: names
            SystemOperation(to_process=True, name="op1.1", duration=TimeUnit(10)),
            SystemOperation(to_process=False, name="wait1", duration=TimeUnit(25)),
            SystemOperation(to_process=True, name="op1.2", duration=TimeUnit(10))
        ]),
        Task(operations=[
            SystemOperation(to_process=True, name="op2.1", duration=TimeUnit(80)),
            SystemOperation(to_process=False, name="wait2.1", duration=TimeUnit(25)),
            SystemOperation(to_process=True, name="op2.2", duration=TimeUnit(80)),
            SystemOperation(to_process=False, name="wait2.2", duration=TimeUnit(10)),
            SystemOperation(to_process=True, name="op2.3", duration=TimeUnit(120))
        ])
    ])
]

orchestrator = Orchestrator(cores_count=2, processing_mode=Mode.SYNC)

orchestrator.process(sagas)
