"""
Module for running LAMMPS
"""

import os
import subprocess
from pathlib import Path
from contextlib import contextmanager

from .files import write_input_deck, read_dumpfile

class LAMMPSError(Exception):
    pass

def run_lammps(dir, records, lammps="lmp", verbose=False):
    """
    Run a LAMMPS simulation for the given records
    (using the given directory as the working dir)

    You can set the path to the LAMMPS executable with
    `lammps`, and toggle whether or not to show the
    LAMMPS output with `verbose`.
    """

    dir = Path(dir).resolve()

    write_input_deck(dir, records)

    with cd_context(dir):
        proc = subprocess.run(
            [lammps, '-in', 'in.input'],
            stdout=(None if verbose else subprocess.DEVNULL)
        )
        if proc.returncode != 0:
            raise LAMMPSError(f"Exited with error. (exit code: {proc.returncode}")

        data = read_dumpfile( Path("sim.dump") )

    return data

# A context-manager to run a block of code
# in a different directory
# Thanks, StackOverflow! https://stackoverflow.com/a/24469659/2827258
@contextmanager
def cd_context(dir):
    original=os.getcwd()
    os.chdir(dir)
    try:
        yield
    finally:
        os.chdir(original)
