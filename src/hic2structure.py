#!/usr/bin/env python3

import argparse
from pathlib import Path

from lib.hic import HIC, HICError
from lib.lammps import run_lammps, LAMMPSError
from lib.out import write_structure, write_contacts
from lib.contact import find_contacts

parser = argparse.ArgumentParser()
parser.add_argument(
    "-r", "--resolution", 
    type=int, default=250000, metavar="NUM",
    help="Bin resolution. (Defaults to 250000)"
)
parser.add_argument(
    "-t", "--threshold",
    type=float, default=3.3, metavar="NUM",
    help="Contact threshold. (Defaults to 3.3)"
)
parser.add_argument(
    "-d", "--directory",
    type=str, default="./lammps_dir", metavar="PATH",
    help="Directory to run in LAMMPS in. (Defaults to './lammps_dir')"
)
parser.add_argument(
    "-o", "--output",
    type=str, default="./out", metavar="PATH",
    help="Output directory. (Defaults to './out')"
)
parser.add_argument(
    "--lammps",
    type=str, default="lmp", metavar="EXEC",
    help="Name of LAMMPS executable to use. (Defaults to 'lmp')"
)
parser.add_argument(
    "-c","--chromosome",
    type=str, default="X", metavar="NAME",
    help="Chromosome to use. (Defaults to 'X')"
)
parser.add_argument(
    "-v", "--verbose",
    help="Increase output verbosity. Can be specified multiple times",
    action="count", default=0
)
parser.add_argument(
    "file",
    help="Input .hic file", type=str
)
args = parser.parse_args()

def log(message, threshold=1):
    """
    Print if verbosity is set high enough
    """
    if args.verbose >= threshold:
        print(message)

log("Loading Hi-C data...")
try:
    data = HIC(args.file)
    records = data.get_contact_records(args.chromosome, args.resolution, args.threshold)
except HICError as e:
    print(f"Error reading contact records: {e}")
    exit(1)

log("Running LAMMPS Simulation...")
try:
    data = run_lammps(
        args.directory,
        records,
        lammps=args.lammps,
        verbose=(args.verbose > 1)
    )
except LAMMPSError as e:
    print(f"Error running LAMMPS: {e}")
    exit(1)

log("Creating Contact Map...")
contacts = find_contacts(data)

log("Writing output files...")
outdir=Path(args.output).resolve()
outdir.mkdir(parents=False, exist_ok=True)

write_structure(
    outdir.joinpath("structure.csv"),
    data
)
write_contacts(
    outdir.joinpath("contactmap.tsv"),
    contacts
)
