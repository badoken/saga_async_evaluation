from pathlib import Path

from jsonpickle import encode
from typing import List, Optional

from src.saga.generation import generate_saga
from src.saga.simple_saga import SimpleSaga

sagas = [
    generate_saga()
    for _
    in range(2000)
]


def export(s: List[SimpleSaga], name: Optional[str] = None):
    serialised = encode(s, indent=4)

    addition_to_name = f"-{name}" if name is not None else ""

    output_dir = "out"
    file_name = f"{len(s)}sagas{addition_to_name}.json"
    path = Path(__file__).parent.joinpath(output_dir).joinpath(file_name)

    print(f"Writing to file {path}")
    with open(file=path, mode="w") as file:
        file.write(serialised)


export(sagas)
