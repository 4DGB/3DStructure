
import argparse
from pathlib import Path
import sys

from .types import Settings
from .hic import HIC, HICError
from .lammps import LAMMPSError, run_lammps
from .contacts import contact_records_to_set
from .out import write_structure

########################
# GLOBALS
########################

verbose=False

########################
# HELPER FUNCTIONS
########################

def settings_from_args(args: argparse.Namespace) -> Settings:
    return {
        'chromosome': args.chromosome,
        'resolution': args.resolution,
        'count_threshold': args.count,
        'distance_threshold': 0, # Unused in the main script 
        'bond_coeff': args.bond_coeff,
        'timesteps': args.timesteps
    }

def log_info(message):
    '''
    Log a message to stderr (if verbose is True)
    '''
    if not verbose:
        return

    print(
        f"\033[1m[\033[94m>\033[0m\033[1m]:\033[0m {message}",
        file=sys.stderr, flush=True
    )

def log_error(message):
    '''
    Log an error message to stderr
    '''
    prefix = "\033[1m[\033[31mERROR\033[0m\033[1m]:\033[0m" \
        if verbose else "error:"

    print(f"{prefix} {message}")

########################
# PARSE ARGUMENTS
########################

parser = argparse.ArgumentParser(
    prog="python3 -m hic2structure",
    description="hic2structure: Uses LAMMPS to generate structures from Hi-C data."
)
parser.add_argument(
    "--resolution", 
    type=int, default=200000, metavar="NUM", dest="resolution",
    help="Bin resolution. (Defaults to 200000)"
)
parser.add_argument(
    "--count-threshold",
    type=float, default=2.0, metavar="NUM", dest="count",
    help="Threshold for reading contacts from Hi-C file. "\
        "Records with a count lower than this are exluced. (Defaults to 2.0)"
)
parser.add_argument(
    "-o", "--output",
    type=str, default="./out", metavar="PATH", dest="output",
    help="Output directory. (Defaults to './out')"
)
parser.add_argument(
    "--lammps",
    type=str, default="lmp", metavar="NAME", dest="lammps",
    help="Name of LAMMPS executable to use. (Defaults to 'lmp')"
)
parser.add_argument(
    "--chromosome",
    type=str, default="X", metavar="NAME", dest="chromosome",
    help="Chromosome to use. (Defaults to 'X')"
)
parser.add_argument(
    "--bond-coeff",
    type=int, default=55, metavar="NUM", dest="bond_coeff",
    help="FENE bond coefficient. This affects the maximum allowed length of"\
        " bonds in the LAMMPS simulation. If LAMMPS gives errors about bad"\
        " bad FENE bonds, try increasing this value. (Defaults to 55)"
)
parser.add_argument(
    "--timesteps",
    type=int, default=1000000, metavar="NUM", dest="timesteps",
    help="Number of timesteps to run in LAMMPS"
)
parser.add_argument(
    "-v", "--verbose",
    help="Enable verbose output",
    action="store_true", default=False
)

parser.add_argument(
    "file",
    help="Input .hic file", type=str
)

args = parser.parse_args()
verbose = args.verbose
outdir  = Path(args.output)
settings = settings_from_args(args)

########################
# MAIN
########################

try:
    hic = HIC( Path(args.file) )
    inputs = contact_records_to_set( hic.get_contact_records(settings) )
    log_info(f"Loaded \033[1m{len(inputs)}\033[0m contact records from Hi-C file.")
except HICError as e:
    log_error(f"Error reading contact records: {e}")
    exit(1)

outdir.mkdir(parents=True, exist_ok=True)

try:
    log_info(f"Running LAMMPS (this might take a while)...")
    lammps_data = run_lammps(inputs, settings, args.lammps, copy_log_to=outdir/'sim.log')
    log_info(f"LAMMPS finished.")
except LAMMPSError as e:
    log_error(e)
    exit(1)

last_timestep = lammps_data[ sorted(lammps_data.keys())[-1] ]

structure_path = outdir/'structure.csv'
write_structure( structure_path, last_timestep )
log_info(f"Saved structure data to \033[1m{structure_path}\033[0m.")
