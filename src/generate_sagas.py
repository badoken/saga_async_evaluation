from os import makedirs
from os.path import dirname
from pathlib import Path

from jsonpickle import encode
from typing import List, Optional, Tuple

from src.saga.generation import generate_saga
from src.saga.simple_saga import SimpleSaga


def _export(s: List[SimpleSaga], name: Optional[str] = None) -> str:
    serialised = encode(s, indent=4)

    addition_to_name = f"-{name}" if name is not None else ""

    output_dir = "../out"
    file_name = f"{len(s)}sagas{addition_to_name}.json"
    path = Path(__file__).parent.joinpath(output_dir).joinpath(file_name)

    print(f"Writing to file {path}")
    try:
        makedirs(dirname(path))
    except FileExistsError:
        pass  # ignoring

    with open(file=path, mode="w") as file:
        file.write(serialised)

    return file_name


def generate_and_export(number: int = 2000, name: Optional[str] = None) -> Tuple[List[SimpleSaga], str]:
    sagas = [
        generate_saga()
        for _
        in range(number)
    ]
    print(f"Generated {number} sagas")

    output_file = _export(sagas, name)

    print(f"Sagas exported to {output_file}")

    return sagas, output_file
