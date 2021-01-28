from pathlib import Path
from typing import List

from jsonpickle import decode

from src.saga.simple_saga import SimpleSaga
from src.sys.system import ProcessingMode
from start_simulation import run_simulation

sagas_file_name = "5000sagas.json"
output_dir = "out"

path = Path(__file__).parent.joinpath(output_dir).joinpath(sagas_file_name)
with open(file=path, mode="r") as file:
    serialised_sagas = file.read()
_sagas: List[SimpleSaga] = decode(serialised_sagas)
print(f"Have read {len(_sagas)} sagas from {sagas_file_name}")

run_simulation(
    sagas=_sagas,
    processors=[1, 2],
    number_of_sagas_sets=[1, 2, 1, 3],  # TODO
    thread_orchestrators_modes=[ProcessingMode.FIXED_POOL_SIZE, ProcessingMode.OVERLOADED_PROCESSORS],
    coroutine_orchestrator=True
)
