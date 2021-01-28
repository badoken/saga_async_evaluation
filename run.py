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

run_simulation(
    sagas=_sagas,
    processors=[20],
    number_of_sagas_sets=[50, 100, 200, 500, 1000],
    coroutine_orchestrator=True
)