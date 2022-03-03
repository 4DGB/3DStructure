"""
Module for writing output files
"""

import csv
from operator import concat

from pathlib import Path

def write_structure(path: Path, data):
    """
    Write out a csv file with structure data
    from the given LAMMPS output
    """
    with open(path, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['id','x','y','z'])
        
        last_timestep = sorted( data.keys() )[-1]
        for row in data[last_timestep]:
            writer.writerow(row[:4])

def write_contacts(path: Path, contacts):
    """
    Write out a tsv file wiht contact map data
    """
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

            # Include a zero for where each value contacts itself
            write_new_row( (x,x), 0.0 )
            write_new_row( (y,y), 0.0 )
            # Include both "sides" of the contact map
            write_new_row( (x, y), row[2] )
            write_new_row( (y, x), row[2] )
