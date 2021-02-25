from src.generate_sagas import generate_and_export
from src.sys.system import ProcessingMode
from src.start_simulation import run_simulation

sagas, _ = generate_and_export(number=2000)

# sagas_file_name = "2000sagas.json"
# output_dir = "out"
# path = Path(__file__).parent.joinpath(output_dir).joinpath(sagas_file_name)
# with open(file=path, mode="r") as file:
#     serialised_sagas = file.read()
# _sagas: List[SimpleSaga] = decode(serialised_sagas)
# print(f"Have read {len(sagas)} sagas from {sagas_file_name}")

run_simulation(
    sagas=sagas,
    processors=[4, 8, 20, 40, 80],
    number_of_sagas_sets=[1500, 1000, 700, 500, 200, 100, 50],
    thread_orchestrators_modes=[ProcessingMode.FIXED_POOL_SIZE, ProcessingMode.OVERLOADED_PROCESSORS],
    coroutine_orchestrator=True
)
