import multiprocessing
import os
from asyncio import Future
from concurrent.futures.thread import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime
from multiprocessing import cpu_count
from pathlib import Path
from signal import signal, SIGINT
from typing import List, Any, Optional, Callable, TextIO

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


class _SimulationRunner:
    def __init__(
            self,
            sagas: List[SimpleSaga],
            processors: List[int],
            number_of_sagas_sets: Optional[List[int]] = None,
            thread_orchestrators_modes: List[ProcessingMode] = [],
            coroutine_orchestrator: bool = False
    ):
        self.sagas: List[SimpleSaga] = sagas
        self.processors: List[int] = processors
        self.number_of_sagas_sets: List[int] = number_of_sagas_sets if number_of_sagas_sets is not None else [
            len(sagas)]
        self.thread_orchestrators_modes: List[ProcessingMode] = thread_orchestrators_modes
        self.coroutine_orchestrator: bool = coroutine_orchestrator
        self.output: Optional[TextIO] = None

    def _sagas_copy(self, number: int) -> List[SimpleSaga]:
        return deepcopy(self.sagas[:number])

    def run(self):
        this_machine_processors_to_use: int = min(self._number_of_simulations, multiprocessing.cpu_count())

        now = datetime.now().strftime("%Y.%m.%d_%H-%M-%S")
        with open(f"out/{now}.log", mode="w") as self.output:
            print(f"Running simulation in {this_machine_processors_to_use} threads")
            self._store_intro()

            with ThreadPoolExecutor(max_workers=this_machine_processors_to_use) as executor:
                self._run_simulations_in_executor(executor)

            self._store_line("Simulation successfully finished!")
            print("Simulation successfully finished!")

    def _run_simulations_in_executor(self, executor: ThreadPoolExecutor):
        simulation_futures: List[Future] = []
        for number_of_sagas in self.number_of_sagas_sets:

            def run_in_parallel(orchestrator_to_run: Orchestrator, short_name: str):
                sagas_to_process = self._sagas_copy(number_of_sagas)
                print(f"Submitting processing of {short_name} with {len(sagas_to_process)} sagas")
                simulation_futures.append(
                    executor.submit(
                        lambda: LogContext.run_logging(
                            log_name=short_name,
                            action=lambda: orchestrator_to_run.process(sagas_to_process),
                            report_publisher=lambda report: self._store_line(str(report))
                        )
                    )
                )

            for number_of_processors in self.processors:
                for mode in self.thread_orchestrators_modes:
                    orchestrator = _threads_orchestrator(processors=number_of_processors, mode=mode)
                    run_in_parallel(
                        orchestrator_to_run=orchestrator,
                        short_name=f"{orchestrator.name()}[p={number_of_processors}, s={number_of_sagas}]"
                    )
                if self.coroutine_orchestrator:
                    run_in_parallel(
                        orchestrator_to_run=_coroutines_orchestrator(processors=number_of_processors),
                        short_name=f"async[p={number_of_processors}, s={number_of_sagas}]"
                    )
        finished: int = 0
        while simulation_futures:
            self._display_progress_bar(current=finished, total=self._number_of_simulations)
            simulation_futures.pop(0).result()
            finished += 1

    def _store_intro(self):
        self._store_line(f"Running simulation on the next dataset:")
        self._store_line(f"* processors={self.processors}")
        self._store_line(f"* number of sagas per simulation={self.number_of_sagas_sets}")
        self._store_line(f"* thread orchestrators={self.thread_orchestrators_modes}")
        self._store_line(f"* coroutine orchestrator used={self.coroutine_orchestrator}")
        self._store_line(f"* number of simulations to run={self._number_of_simulations}")

    def _store_line(self, line: str):
        self.output.write(line + "\n")

    @property
    def _number_of_simulations(self):
        number_of_simulations_per_orchestrator: int = len(self.number_of_sagas_sets) * len(self.processors)

        simulations_per_thread_orch: int = number_of_simulations_per_orchestrator * len(self.thread_orchestrators_modes)
        simulations_for_coroutine_orch: int = number_of_simulations_per_orchestrator if self.coroutine_orchestrator else 0

        return min(
            cpu_count() + 1,
            simulations_per_thread_orch + simulations_for_coroutine_orch
        )

    @staticmethod
    def _display_progress_bar(current: int, total: int, bar_length: int = 20):
        percent = float(current) * 100 / total

        arrow = '-' * int(percent / 100 * bar_length - 1) + '>'
        spaces = ' ' * (bar_length - len(arrow))
        progress_visualisation = arrow + spaces

        print(f'Progress: [{progress_visualisation}] {int(percent)} %   # can hang like that for some time', end='\r')


def run_simulation(
        sagas: List[SimpleSaga],
        processors: List[int],
        number_of_sagas_sets: Optional[List[int]] = None,
        thread_orchestrators_modes: List[ProcessingMode] = [],
        coroutine_orchestrator: bool = False
):
    _SimulationRunner(
        sagas=sagas,
        processors=processors,
        number_of_sagas_sets=number_of_sagas_sets,
        thread_orchestrators_modes=thread_orchestrators_modes,
        coroutine_orchestrator=coroutine_orchestrator
    ).run()
