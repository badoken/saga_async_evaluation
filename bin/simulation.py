from copy import deepcopy
from threading import Thread
from typing import List

from saga.generation import generate_saga
from saga.simple_saga import SimpleSaga
from src.log import LogContext
from saga.orchestration import CoroutinesOrchestrator
from src.saga.orchestration import ThreadedOrchestrator
from src.sys.operation_system import ProcessingMode
from src.sys.time.duration import Duration

_sagas = [
    generate_saga()
    for _
    in range(100)
]


def sagas_copy() -> List[SimpleSaga]:
    return deepcopy(_sagas)


overloaded_threads_orchestrator = ThreadedOrchestrator(processors_number=2, processing_mode=ProcessingMode.OVERLOADED_PROCESSORS)
fixed_pool_threads_orchestrator = ThreadedOrchestrator(processors_number=2, processing_mode=ProcessingMode.FIXED_POOL_SIZE)
coroutines_orchestrator = CoroutinesOrchestrator(processors_number=2)

threads: List[Thread] = []


def run_in_parallel(orchestrator, short_name: str):
    new_thread = Thread(
        name=short_name,
        target=lambda: LogContext.run_logging(
            log_name=short_name,
            action=lambda: orchestrator.process(sagas_copy()),
            publish_report_every=Duration(millis=100)
        )
    )
    threads.append(new_thread)
    new_thread.start()


run_in_parallel(
    orchestrator=overloaded_threads_orchestrator,
    short_name="overloaded"
)

run_in_parallel(
    orchestrator=fixed_pool_threads_orchestrator,
    short_name="fixed_pool"
)

run_in_parallel(
    orchestrator=coroutines_orchestrator,
    short_name="async"
)

for thread in threads:
    thread.join()
