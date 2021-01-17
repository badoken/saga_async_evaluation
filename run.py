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


def overloaded_orchestrator(processors: int) -> ThreadedOrchestrator:
    return ThreadedOrchestrator(processors_number=processors,
                                processing_mode=ProcessingMode.OVERLOADED_PROCESSORS)


def fixed_pool_orchestrator(processors: int) -> ThreadedOrchestrator:
    return ThreadedOrchestrator(processors_number=processors,
                                processing_mode=ProcessingMode.FIXED_POOL_SIZE)


def coroutines_orchestrator(processors: int) -> CoroutinesOrchestrator:
    return CoroutinesOrchestrator(processors_number=processors)


this_machine_processors_number = cpu_count() + 1

_sagas = [
    generate_saga()
    for _
    in range(1000)
]


def sagas_copy(number_of_sagas: int) -> List[SimpleSaga]:
    return deepcopy(_sagas[:number_of_sagas])


print(f"Running simulation on {this_machine_processors_number} processors")
with ThreadPoolExecutor(max_workers=this_machine_processors_number) as executor:
    simulation_futures: List[Future] = []

    for number_of_sagas in [50, 100, 200, 500, 1000]:

        def run_in_parallel(orchestrator, short_name: str):
            simulation_futures.append(
                executor.submit(
                    lambda: LogContext.run_logging(
                        log_name=short_name,
                        action=lambda: orchestrator.process(sagas_copy(number_of_sagas))
                    )
                )
            )


        for number_of_processors in [4, 8, 20, 40]:
            run_in_parallel(
                orchestrator=overloaded_orchestrator(processors=number_of_processors),
                short_name=f"overloaded[p={number_of_processors}, s={number_of_sagas}]"
            )

            run_in_parallel(
                orchestrator=fixed_pool_orchestrator(processors=number_of_processors),
                short_name=f"fixed_pool[p={number_of_processors}, s={number_of_sagas}]"
            )

            run_in_parallel(
                orchestrator=coroutines_orchestrator(processors=number_of_processors),
                short_name=f"async[p={number_of_processors}, s={number_of_sagas}]"
            )

    while simulation_futures:
        simulation_futures.pop(0).result()
