from asyncio import Future
from concurrent.futures.thread import ThreadPoolExecutor
from copy import deepcopy
from multiprocessing import cpu_count
from pathlib import Path
from typing import List, Any, Optional, Callable

from jsonpickle import decode

from src.log import LogContext
from src.saga.orchestration import CoroutinesOrchestrator, Orchestrator
from src.saga.orchestration import ThreadedOrchestrator
from src.saga.simple_saga import SimpleSaga
from src.sys.system import ProcessingMode


def _threads_orchestrator(processors: int, mode: ProcessingMode) -> ThreadedOrchestrator:
    return ThreadedOrchestrator(processors_number=processors, processing_mode=mode)


def _coroutines_orchestrator(processors: int) -> CoroutinesOrchestrator:
    return CoroutinesOrchestrator(processors_number=processors)


def run_simulation(
        sagas: List[SimpleSaga],
        processors: List[int],
        number_of_sagas_sets: Optional[List[int]] = None,
        thread_orchestrators_modes: List[ProcessingMode] = [],
        coroutine_orchestrator: bool = False
):
    number_of_sagas_sets: List[int] = \
        number_of_sagas_sets \
            if number_of_sagas_sets is not None \
            else [len(sagas)]

    def _sagas_copy(number: int) -> List[SimpleSaga]:
        return deepcopy(sagas[:number])

    this_machine_processors_to_use = _number_of_processors_to_run_simulation(
        coroutine_orchestrator,
        number_of_sagas_sets,
        processors,
        thread_orchestrators_modes
    )
    print(f"Running simulation on {this_machine_processors_to_use} processors")
    with ThreadPoolExecutor(max_workers=this_machine_processors_to_use) as executor:
        simulation_futures: List[Future] = []

        for number_of_sagas in number_of_sagas_sets:

            def run_in_parallel(orch: Orchestrator, short_name: str):
                sagas_to_process = _sagas_copy(number_of_sagas)
                print(f"Submitting processing of {short_name} with {len(sagas_to_process)} sagas")
                simulation_futures.append(
                    executor.submit(
                        lambda: LogContext.run_logging(
                            log_name=short_name,
                            action=lambda: orch.process(sagas_to_process)
                        )
                    )
                )

            for number_of_processors in processors:
                for mode in thread_orchestrators_modes:
                    orchestrator = _threads_orchestrator(processors=number_of_processors, mode=mode)
                    run_in_parallel(
                        orch=orchestrator,
                        short_name=f"{orchestrator.name()}[p={number_of_processors}, s={number_of_sagas}]"
                    )
                if coroutine_orchestrator:
                    run_in_parallel(
                        orch=_coroutines_orchestrator(processors=number_of_processors),
                        short_name=f"async[p={number_of_processors}, s={number_of_sagas}]"
                    )

        while simulation_futures:
            simulation_futures.pop(0).result()


def _number_of_processors_to_run_simulation(
        coroutine_orchestrator: bool,
        number_of_sagas_sets: List[int],
        processors: List[int],
        thread_orchestrators_modes: List[ProcessingMode]
):
    number_of_simulations_per_orchestrator: int = len(number_of_sagas_sets) * len(processors)

    simulations_per_thread_orch: int = number_of_simulations_per_orchestrator * len(thread_orchestrators_modes)
    simulations_for_coroutine_orch: int = number_of_simulations_per_orchestrator if coroutine_orchestrator else 0

    return min(
        cpu_count() + 1,
        simulations_per_thread_orch + simulations_for_coroutine_orch
    )
