#!/usr/bin/env python3

import argparse
from pathlib import Path

from lib.hic import HIC
from lib.lammps import run_lammps
from lib.out import write_structure, write_contacts
from lib.contact import find_contacts

parser = argparse.ArgumentParser()
parser.add_argument(
    "-r", "--resolution", 
    help="Bin resolution", type=int, default=250000
)
parser.add_argument(
    "-t", "--threshold",
    help="Contact threshold", type=float, default=3.3
)
parser.add_argument(
    "-d", "--directory",
    help="LAMMPS run directory", type=str, default="./lammps_dir"
)
parser.add_argument(
    "-o", "--output",
    help="Output directory", type=str, default="./out"
)
parser.add_argument(
    "--lammps",
    help="LAMMPS executable to use", type=str, default="lmp"
)
parser.add_argument(
    "-c","--chromosome",
    help="Chromosome to use", type=str, default="X"
)
parser.add_argument(
    "-v", "--verbose",
    help="Increase output verbosity (can be specified multiple times",
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
data = HIC(args.file)
records = data.get_contact_records(args.chromosome, args.resolution, args.threshold)

log("Running LAMMPS Simulation...")
data = run_lammps(
    args.directory,
    records,
    lammps=args.lammps,
    verbose=(args.verbose > 1)
)

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
