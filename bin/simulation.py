from copy import deepcopy
from threading import Thread
from typing import List

from saga.generation import generate_saga
from src.log import LogContext
from src.saga.coroutines_orchestrator import CoroutinesOrchestrator
from src.saga.threaded_orchestrator import ThreadedOrchestrator
from src.sys.operation_system import ProcessingMode

sagas = [
    generate_saga(data_preservation=True)
    for _
    in range(4)
]

overloaded_threads_orchestrator = ThreadedOrchestrator(cores_count=2, processing_mode=ProcessingMode.OVERLOADED_CORES)
fixed_pool_threads_orchestrator = ThreadedOrchestrator(cores_count=2, processing_mode=ProcessingMode.FIXED_POOL_SIZE)
coroutines_orchestrator = CoroutinesOrchestrator(cores_count=2)

threads: List[Thread] = []


def run_simulation_in_parallel(orchestrator, short_name: str, full_name: str):
    new_thread = Thread(
        name=short_name,
        target=lambda:
        print(full_name + " done in " + str(
            LogContext.run_logging(
                log_name=short_name,
                action=lambda: orchestrator.process(deepcopy(sagas))
            )
        ))
    )
    threads.append(new_thread)
    new_thread.start()


run_simulation_in_parallel(
    orchestrator=overloaded_threads_orchestrator,
    short_name="overloaded",
    full_name="Overloaded system"
)

run_simulation_in_parallel(
    orchestrator=fixed_pool_threads_orchestrator,
    short_name="fixed_pool",
    full_name="Fixed thread pool"
)

run_simulation_in_parallel(
    orchestrator=coroutines_orchestrator,
    short_name="async",
    full_name="Coroutines"
)

for thread in threads:
    thread.join()
