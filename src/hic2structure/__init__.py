from pathlib import Path

from .types import Settings
from .hic import HIC
from .lammps import run_lammps
from .contacts import find_contacts
from .out import write_contacts, write_structure

def process_hic(infile: Path, outdir: Path, settings: Settings):
    '''
    Run LAMMPS on a given Hi-C file and place output in the specifed
    directory.

    Returns a dict with paths to various output files.
    '''
    hic = HIC( infile )
    input_records = hic.get_contact_records(settings)

    outdir.mkdir(parents=True, exist_ok=True)

    lammps_data = run_lammps(input_records, settings, copy_log_to=outdir/'sim.log')

    last_timestep = lammps_data[ sorted(lammps_data.keys())[-1] ]

    output_records = find_contacts(last_timestep, settings)

    write_structure( outdir/'structure.csv', last_timestep )

    write_contacts( outdir/'contactmap.tsv', output_records )

    return {
        'structure':  (outdir/'structure.csv').resolve(),
        'contactmap': (outdir/'contactmap.tsv').resolve(),
        'log':        (outdir/'sim.log').resolve(),
    }
