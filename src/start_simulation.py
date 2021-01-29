from copy import deepcopy
from datetime import datetime
from multiprocessing import cpu_count, Pool
from multiprocessing.pool import ApplyResult
from typing import List, Any, Optional, TextIO

from src.log import LogContext, Report
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

    def run_simulations(self):
        this_machine_processors_to_use: int = min(self._number_of_simulations, cpu_count())

        now = datetime.now().strftime("%Y.%m.%d_%H-%M-%S")
        with open(f"out/{now}.log", mode="w") as self.output:
            print(f"Running {self._number_of_simulations} simulation in {this_machine_processors_to_use} processors")
            self._store_intro()

            with Pool(processes=this_machine_processors_to_use) as pool:
                self._run_simulations_in_pool(pool)
                pool.close()
                pool.join()

            self._store_line("Simulation successfully finished!")
            print("\nSimulation successfully finished!")

    def _run_simulations_in_pool(self, pool: Pool):
        finished: List[int] = [0]
        results: List[ApplyResult] = []

        self._display_progress_bar(current=0, total=self._number_of_simulations)

        def callback(report: Report):
            finished[0] = finished[0] + 1
            self._display_progress_bar(current=finished[0], total=self._number_of_simulations)
            self._store_line(str(report))

        def error_callback(r: Any):
            print(f"Simulation error: {r}")

        for number_of_sagas in self.number_of_sagas_sets:
            sagas_to_process = self._sagas_copy(number_of_sagas)
            for number_of_processors in self.processors:
                for mode in self.thread_orchestrators_modes:
                    orchestrator = _threads_orchestrator(processors=number_of_processors, mode=mode)
                    results.append(
                        pool.apply_async(
                            self._run_simulation,
                            args=(orchestrator, number_of_processors, sagas_to_process),
                            callback=callback,
                            error_callback=error_callback
                        )
                    )
                if self.coroutine_orchestrator:
                    orchestrator = _coroutines_orchestrator(processors=number_of_processors)
                    results.append(
                        pool.apply_async(
                            self._run_simulation,
                            args=(orchestrator, number_of_processors, sagas_to_process),
                            callback=callback
                        )
                    )

        for result in results:
            result.wait()

    @staticmethod
    def _run_simulation(orchestrator: Orchestrator, processors: int, sagas: List[SimpleSaga]) -> Report:
        name = f"{orchestrator.name()}, {processors}p, {len(sagas)}s"

        result: List[Report] = []
        LogContext.run_logging(
            log_name=name,
            action=lambda: orchestrator.process(sagas),
            report_publisher=lambda report: result.append(report)
        )
        return result[0]

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

        simulations_per_all_thread_orchs: int = \
            number_of_simulations_per_orchestrator * len(self.thread_orchestrators_modes)

        simulations_for_coroutine_orch: int = \
            number_of_simulations_per_orchestrator if self.coroutine_orchestrator else 0

        return simulations_per_all_thread_orchs + simulations_for_coroutine_orch

    @staticmethod
    def _display_progress_bar(current: int, total: int, bar_length: int = 20):
        percent = float(current) * 100 / total

        arrow = '-' * int(percent / 100 * bar_length - 1) + '>'
        spaces = ' ' * (bar_length - len(arrow))
        progress_visualisation = arrow + spaces

        print(f'Progress: [{progress_visualisation}] {int(percent)} %   # can hang like that for a long time', end='\r')


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
    ).run_simulations()
