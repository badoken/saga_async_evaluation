from copy import deepcopy

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

overloaded = LogContext.run_logging(
    log_name="Overloaded",
    action=lambda: overloaded_threads_orchestrator.process(deepcopy(sagas))
)
print("Overloaded system is done in " + str(overloaded))

fixed_pool = LogContext.run_logging(
    log_name="Fixed pool",
    action=lambda: fixed_pool_threads_orchestrator.process(deepcopy(sagas))
)
print("Fixed thread pool is done in " + str(fixed_pool))

coroutines = LogContext.run_logging(
    log_name="Coroutines",
    action=lambda: coroutines_orchestrator.process(deepcopy(sagas))
)
print("Coroutines are done in " + str(coroutines))