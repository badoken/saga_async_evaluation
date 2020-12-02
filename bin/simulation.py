from bin.saga.orchestration import Orchestrator
from bin.saga.simple_saga import SimpleSaga
from bin.sys.operation_system import ProcessingMode
from bin.sys.task import Task, SystemOperation
from bin.sys.time import Duration

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

orchestrator = Orchestrator(cores_count=2, processing_mode=ProcessingMode.OVERLOADED_CORES)

print("Orchestration is complete in " + str(orchestrator.process(sagas)))
