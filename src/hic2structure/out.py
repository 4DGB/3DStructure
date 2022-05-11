"""
Module for writing output files
"""

import csv

from pathlib import Path
from .types import LAMMPSTimestep, ContactRecords, ContactSet

def write_structure(path: Path, data: LAMMPSTimestep):
    """
    Write out a csv file with structure data
    from the given LAMMPS output
    """
    with open(path, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['id','x','y','z'])

        for row in data:
            writer.writerow(row[:4])

def write_contact_records(path: Path, contacts: ContactRecords):
    """
    Write out a tsv file wiht contact map data
    """
    max_value = max( contacts[:,2] )

    with open(path, 'w') as f:
        writer = csv.writer(f, delimiter='\t')
        seen = set()

        # Write out a contact record if that pair of coordinates
        # hasn't been seen before
        def write_new_row(coords, value):
            if coords not in seen:
                writer.writerow([coords[0], coords[1], value])
                seen.add(coords)

        for row in contacts:
            x = int(row[0])
            y = int(row[1])

            # Use the maximum value for where each value contacts itself
            write_new_row( (x,x), max_value )
            write_new_row( (y,y), max_value )
            # Include both "sides" of the contact map
            write_new_row( (x, y), row[2] )
            write_new_row( (y, x), row[2] )

def write_contact_set(path: Path, contacts: ContactSet):
    """
    Write out a tsv file with contact record coordinates
    """
    with open(path, 'w') as f:
        writer = csv.writer(f, delimter='\t')
        seen = set()

        # Write out a contact record if that pair of coordinates
        # hasn't been seen before
        def write_new_row(coords):
            if coords not in seen:
                writer.writerow([coords[0], coords[1]])
                seen.add(coords)

        for row in contacts:
            x = row[0]
            y = row[1]
            write_new_row( (x,y) )
            write_new_row( (y,x) )
