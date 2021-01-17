from asyncio import Future
from concurrent.futures.thread import ThreadPoolExecutor
from copy import deepcopy
from multiprocessing import cpu_count
from typing import List

from src.saga.generation import generate_saga
from src.saga.orchestration import CoroutinesOrchestrator
from src.saga.simple_saga import SimpleSaga
from src.log import LogContext
from src.saga.orchestration import ThreadedOrchestrator
from src.sys.system import ProcessingMode

this_machine_processors_number = cpu_count() + 1

with ThreadPoolExecutor(max_workers=this_machine_processors_number) as executor:
    print(f"Running simulation on {this_machine_processors_number} processors")

    _sagas = [
        generate_saga()
        for _
        in range(40)
    ]


    def sagas_copy() -> List[SimpleSaga]:
        return deepcopy(_sagas)


    def overloaded_orchestrator(processors: int) -> ThreadedOrchestrator:
        return ThreadedOrchestrator(processors_number=processors, processing_mode=ProcessingMode.OVERLOADED_PROCESSORS)


    def fixed_pool_orchestrator(processors: int) -> ThreadedOrchestrator:
        return ThreadedOrchestrator(processors_number=processors, processing_mode=ProcessingMode.FIXED_POOL_SIZE)


    def coroutines_orchestrator(processors: int) -> CoroutinesOrchestrator:
        return CoroutinesOrchestrator(processors_number=processors)


    simulation_futures: List[Future] = []


    def run_in_parallel(orchestrator, short_name: str):
        simulation_futures.append(
            executor.submit(
                lambda: LogContext.run_logging(
                    log_name=short_name,
                    action=lambda: orchestrator.process(sagas_copy())
                )
            )
        )


    for number_of_processors in range(2, 10, 2):
        run_in_parallel(
            orchestrator=overloaded_orchestrator(processors=number_of_processors),
            short_name=f"overloaded[{number_of_processors}]"
        )

        run_in_parallel(
            orchestrator=fixed_pool_orchestrator(processors=number_of_processors),
            short_name=f"fixed_pool[{number_of_processors}]"
        )

        run_in_parallel(
            orchestrator=coroutines_orchestrator(processors=number_of_processors),
            short_name=f"async[{number_of_processors}]"
        )

    while simulation_futures:
        simulation_futures.pop(0).result()
